# Motiva Challenge — Dynamic Programming

Entrega de Dynamic Programming, turma **2ESPS**.

- Gabriel Cutrim — RM 568059
- Guilherme Pereira — RM 567487
- Gustavo Firmino Barbosa — RM 566903

O [notebook.ipynb](notebook.ipynb) contém código executado, resultados e
interpretações: três versões de acumulação de criticidade, ranking, modelagem
em grafo, BFS, Dijkstra, A* e planejamento de turno.

## Executar

Python 3.13 foi utilizado. Após clonar este repositório:

```powershell
python -m pip install -r requirements.txt
python executar.py
python -m unittest discover -s . -p test_algoritmos.py -v
```

Também é possível abrir o notebook no Jupyter ou VS Code e executar todas as
células. Todos os dados usados estão neste repositório; não é necessário acessar
outro projeto ou baixar a planilha original para reproduzir os experimentos.
`resultados/` contém as saídas exportadas durante a execução.

## Dados reais e dados simulados

A [pasta original fornecida ao grupo](https://drive.google.com/drive/folders/1S7f7mk8bg0clGllzc8GTgvakvvnJ3NMP)
contém histórico de manutenção. A planilha `ecr_09-26.XLSX` tem 104.119 registros
e 22 colunas, mas não contém as leituras físicas previstas no enunciado.

`dados/historico_avarias.csv` preserva todas as linhas, com apenas sete campos
usados nesta entrega: nota, indicador de indisponibilidade, local de instalação,
data/hora de início e data/hora de fim. Uma oitava coluna, `assinatura_registro`,
é uma assinatura técnica das 22 colunas normalizadas, para manter a mesma
identificação de duplicatas sem publicar os textos livres. A origem, a seleção de
campos e os hashes dos arquivos constam de `dados/procedencia_historico.json`.

O notebook analisa duas situações **separadamente**:

1. **Histórico real:** a soma de durações registradas de avarias é um indicador
   alternativo de carga histórica; não é degradação física nem probabilidade de falha.
2. **Sensores SIMULADOS:** 22 equipamentos fictícios e 2.112 leituras de vibração,
   temperatura, corrente, tensão, óleo e velocidade. Servem para demonstrar o
   fluxo de sensores até o ranking e o plano. Não são medições da Motiva.

A simulação foi solicitada pelo grupo diante da ausência de sensores no material
fornecido. A aceitação dessa adaptação depende do professor.
`simulacao.py` documenta o gerador com semente 566903. A base bruta artificial
contém duas duplicatas e três lacunas internas de temperatura intencionais;
`preparar()` remove essas cópias e interpola as lacunas por equipamento.
Extremos válidos são mantidos. Unidades, referências, escalas e pesos são hipóteses
didáticas, descritas no JSON e em `dados/LEIA_ME_SIMULACAO.md`.

## Criticidade: recursão, memoização e tabulação

A recorrência é `D(0)=0; D(n)=D(n−1)+incremento[n−1]`.
`algoritmos.py` implementa `recursiva`, `memoizada` com dicionário e `tabulacao`.
As três têm tempo O(n) e espaço O(n), incluindo pilha ou tabela. Não há explosão
exponencial nesta recorrência: cada passo chama apenas um subproblema. Memoização
beneficia consultas repetidas a prefixos; cache só pode ser reutilizado para a
mesma sequência imutável.

No histórico, a janela seleciona avarias iniciadas no último ano disponível e
marcadas `Indisponível = X`. Durações negativas, sem datas ou com datas posteriores
a 18/10/2026 não contribuem; cobertura é exibida em vez de transformar ausência
em zero. O fim é limitado à janela anual. A soma de notas pode incluir intervalos
sobrepostos e não representa indisponibilidade cronológica líquida. Registros
genéricos de estação não são atribuídos a escadas individuais.

Nos sensores artificiais, `sensores.py` calcula desvios normalizados: acima da
referência para vibração, temperatura e corrente; abaixo para óleo; bilaterais
para tensão e velocidade. A média ponderada desses desvios é integrada pelo
método dos trapézios em horas. A primeira leitura contribui zero, e lacunas acima
do limite configurado causam erro. Não se afirma calibração de dano físico.

O notebook verifica a equivalência das três versões em todas as sequências.
No histórico, sequências extensas usam blocos recursivos de até 300 eventos sem
aumentar o limite da pilha; tabulação calcula o ranking integral. Nos sensores
simulados, as três versões processam diretamente as 96 leituras de cada escada.
Os tempos usam sete repetições de cem chamadas, com cache inicialmente vazio.

## Grafo, BFS, Dijkstra e A*

`dados/rede_estacoes.json` descreve uma rede não direcionada com 11 estações da
Linha 4, um terminal e uma base de manutenção didática. Os nomes são apoiados na
[lista de estações da Motiva](https://trilhos.motiva.com.br/linha-4-amarela/estacoes/).
Tempos em minutos, coordenadas esquemáticas, posição da base e a alternativa
viária BASE–PIN são hipóteses; não representam horários oficiais. O vínculo do
código TVS ao terminal junto a Vila Sônia também deve ser validado.

Os arquivos `escadas_estacoes.csv` e `escadas_simuladas_estacoes.csv` vinculam
os equipamentos individuais aos vértices. Os registros genéricos permanecem
auditados, sem criação de equipamentos fictícios na análise real.

BFS encontra menos trechos em O(V+E). Dijkstra usa heap e encontra menor tempo
em O((V+E) log V). As rotas são reconstruídas com predecessores.

A* utiliza `h(v)=distância_esquemática(v,destino)/vmax`, onde
`vmax=max(distância_esquemática(u,v)/peso(u,v))` sobre as arestas. Cada peso é
pelo menos a distância dividida por vmax. Pela desigualdade triangular, a
heurística é consistente e admissível. As coordenadas não são geográficas e
vmax não é uma velocidade operacional real.

A comparação usa o mesmo par origem/destino e encerra ambos os algoritmos ao
retirar o destino da fila. Mostra custos, rotas, expansões e tempos. O preparo da
heurística está incluído no custo de A*. Custos devem coincidir; menos expansões
podem não compensar o custo da heurística numa rede pequena.

## Plano de manutenção

`criar_planejador(grafo, ranking)` devolve `planejar_turno(base, horas)`.
A função tenta atender na ordem de criticidade, calculando deslocamentos a
partir da posição atual e reservando tempo para retorno à base. Itens inviáveis
são registrados e o próximo é tentado. Empates usam o identificador da escada.

Considera uma equipe, serviços indivisíveis e 45 minutos por escada. O notebook
também avalia serviços de 30 e 60 minutos e a sensibilidade do ranking a durações
extremas. Trata-se de política gulosa por prioridade; não garante ótimo global.
Pausas, disponibilidade de peças, qualificações e interdições não são modeladas.

## Resultados e interpretação

As interpretações e medições estão nas saídas do notebook. A execução verifica
totais equivalentes entre as recorrências, custos iguais entre A* e Dijkstra e
turnos dentro da jornada, incluindo retorno. Os rankings do histórico real e dos
sensores artificiais não são misturados. Os CSVs e JSONs exportados em
`resultados/` permitem conferir os valores usados nos experimentos.

Os testes cobrem prefixos das recorrências, diferentes objetivos de BFS e
Dijkstra, A* entre todos os pares com vértice desconectado, retorno do turno,
pesos inválidos e integração sensorial com controle de lacunas.
