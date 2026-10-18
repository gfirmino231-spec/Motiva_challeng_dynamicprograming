"""Criticidade por exposição, três recorrências e rotas de manutenção.

O índice é uma hipótese didática, sem validade diagnóstica ou de segurança.
"""
from collections import deque
from heapq import heappop, heappush
from math import hypot, inf, isfinite


def recursiva(valores, n=None):
    """D(0)=0; D(n)=D(n-1)+valores[n-1]. Tempo e pilha O(n)."""
    n = len(valores) if n is None else n
    if not 0 <= n <= len(valores):
        raise ValueError('Prefixo inválido')
    return 0.0 if n == 0 else recursiva(valores, n - 1) + valores[n - 1]


def memoizada(valores, n=None, cache=None):
    """Memoização em dicionário; reutilize cache apenas para a mesma sequência."""
    n = len(valores) if n is None else n
    if not 0 <= n <= len(valores):
        raise ValueError('Prefixo inválido')
    cache = {0: 0.0} if cache is None else cache
    cache.setdefault(0, 0.0)
    if n not in cache:
        cache[n] = memoizada(valores, n - 1, cache) + valores[n - 1]
    return cache[n]


def tabulacao(valores):
    """Retorna todos os prefixos: O(n) tempo/espaço, sem limite de pilha."""
    tabela = [0.0]
    for valor in valores:
        tabela.append(tabela[-1] + valor)
    return tabela


def montar_grafo(vertices, arestas):
    """Lista de adjacência não direcionada, com pesos em minutos."""
    grafo = {v: [] for v in vertices}
    for origem, destino, minutos in arestas:
        if origem not in grafo or destino not in grafo:
            raise ValueError('Aresta com vértice desconhecido')
        if not isfinite(minutos) or minutos <= 0:
            raise ValueError('Peso deve ser finito e positivo')
        grafo[origem].append((destino, minutos))
        grafo[destino].append((origem, minutos))
    return grafo


def reconstruir(pais, origem, destino):
    """Reconstrói o caminho; devolve [] se o destino é inalcançável."""
    if destino not in pais:
        return []
    rota = [destino]
    while rota[-1] != origem:
        rota.append(pais[rota[-1]])
    return rota[::-1]


def bfs(grafo, origem):
    """Menos arestas; retorna distâncias em trechos e predecessores. O(V+E)."""
    if origem not in grafo:
        raise ValueError('Origem inexistente')
    dist, pais, fila = {origem: 0}, {origem: None}, deque([origem])
    while fila:
        atual = fila.popleft()
        for vizinho, _ in grafo[atual]:
            if vizinho not in pais:
                pais[vizinho] = atual
                dist[vizinho] = dist[atual] + 1
                fila.append(vizinho)
    return dist, pais


def dijkstra(grafo, origem, destino=None):
    """Menor tempo com heap: O((V+E) log V); retorna dist, pais, expansões."""
    if origem not in grafo:
        raise ValueError('Origem inexistente')
    dist, pais, fila, expandidos = {origem: 0.0}, {origem: None}, [(0.0, origem)], 0
    while fila:
        custo, atual = heappop(fila)
        if custo != dist[atual]:
            continue
        expandidos += 1
        if atual == destino:
            break
        for vizinho, peso in grafo[atual]:
            candidato = custo + peso
            if candidato < dist.get(vizinho, inf):
                dist[vizinho], pais[vizinho] = candidato, atual
                heappush(fila, (candidato, vizinho))
    return dist, pais, expandidos


def astar(grafo, coordenadas, origem, destino):
    """A* com h=distância euclidiana/vmax, em unidades esquemáticas/minuto.

    vmax=max(distância da aresta/peso). Cada peso >= distância/vmax;
    desigualdade triangular garante consistência e admissibilidade.
    As coordenadas são esquemáticas, não coordenadas geográficas reais.
    """
    if origem not in grafo or destino not in grafo:
        raise ValueError('Vértice inexistente')
    def distancia(a, b):
        return hypot(coordenadas[a][0] - coordenadas[b][0],
                     coordenadas[a][1] - coordenadas[b][1])
    vmax = max((distancia(a, b) / p for a in grafo for b, p in grafo[a]), default=0)
    def h(a):
        return distancia(a, destino) / vmax if vmax else 0.0
    dist, pais = {origem: 0.0}, {origem: None}
    fila, expandidos = [(h(origem), 0.0, origem)], 0
    while fila:
        _, custo, atual = heappop(fila)
        if custo != dist[atual]:
            continue
        expandidos += 1
        if atual == destino:
            return custo, reconstruir(pais, origem, destino), expandidos
        for vizinho, peso in grafo[atual]:
            candidato = custo + peso
            if candidato < dist.get(vizinho, inf):
                dist[vizinho], pais[vizinho] = candidato, atual
                heappush(fila, (candidato + h(vizinho), candidato, vizinho))
    return inf, [], expandidos


def criar_planejador(grafo, ranking):
    """Vincula rede e ranking, devolvendo a função planejar_turno(base, horas)."""
    def planejar_turno(base, horas):
        """Atende por prioridade, verifica deslocamento, serviço e retorno à base.

        Heurística gulosa: pula itens inviáveis e tenta os próximos. Não promete
        ótimo global. Uma equipe, serviços indivisíveis e tempos determinísticos.
        """
        if base not in grafo or not isfinite(horas) or horas < 0:
            raise ValueError('Base ou duração inválida')
        limite, gasto, atual, plano, ignoradas = horas * 60, 0.0, base, [], []
        for item in ranking:
            destino, servico = item['estacao'], float(item['servico_min'])
            if destino not in grafo or not isfinite(servico) or servico <= 0:
                raise ValueError('Estação ou serviço inválido no ranking')
            dist, pais, _ = dijkstra(grafo, atual, destino)
            volta, _, _ = dijkstra(grafo, destino, base)
            ida, retorno = dist.get(destino, inf), volta.get(base, inf)
            if gasto + ida + servico + retorno <= limite:
                plano.append(dict(escada_id=item['escada_id'], estacao=destino,
                                  criticidade=item['criticidade'], saida_min=gasto,
                                  rota=reconstruir(pais, atual, destino),
                                  deslocamento_min=ida, servico_min=servico,
                                  conclusao_min=gasto + ida + servico))
                gasto += ida + servico
                atual = destino
            else:
                ignoradas.append(item['escada_id'])
        dist, pais, _ = dijkstra(grafo, atual, base)
        retorno = dist.get(base, inf)
        return dict(atendimentos=plano, nao_atendidas=ignoradas,
                    rota_retorno=reconstruir(pais, atual, base),
                    retorno_min=retorno, total_min=gasto + retorno,
                    disponivel_min=limite - gasto - retorno)
    return planejar_turno
