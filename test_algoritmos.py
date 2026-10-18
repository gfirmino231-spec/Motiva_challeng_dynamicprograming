"""Verificações de equivalência, rotas e restrições do turno."""
import math
import unittest
import pandas as pd
from sensores import incrementos_sensores, SENSORES
from algoritmos import (recursiva, memoizada, tabulacao, montar_grafo, bfs,
                        dijkstra, astar, reconstruir, criar_planejador)


class AlgoritmosTest(unittest.TestCase):
    def setUp(self):
        self.coords = {'B': (0, 0), 'A': (1, 0), 'C': (2, 0), 'X': (8, 0)}
        self.g = montar_grafo(self.coords, [('B', 'A', 2), ('A', 'C', 2), ('B', 'C', 9)])

    def test_equivalencia_prefixos(self):
        for valores in [[], [0], [1, 2, 3.5], [0.1] * 200]:
            cache = {}
            for n in range(len(valores)+1):
                self.assertAlmostEqual(recursiva(valores, n), memoizada(valores, n, cache))
                self.assertAlmostEqual(recursiva(valores, n), tabulacao(valores)[n])

    def test_bfs_e_dijkstra_objetivos_distintos(self):
        _, pb = bfs(self.g, 'B')
        d, pd, _ = dijkstra(self.g, 'B')
        self.assertEqual(reconstruir(pb, 'B', 'C'), ['B', 'C'])
        self.assertEqual(reconstruir(pd, 'B', 'C'), ['B', 'A', 'C'])
        self.assertEqual(d['C'], 4)
        self.assertEqual(reconstruir(pd, 'B', 'X'), [])

    def test_astar_todos_pares_inclusive_desconectado(self):
        for a in self.g:
            for b in self.g:
                dist, _, _ = dijkstra(self.g, a, b)
                custo, rota, _ = astar(self.g, self.coords, a, b)
                esperado = dist.get(b, math.inf)
                self.assertEqual(custo, esperado)
                if math.isfinite(custo):
                    self.assertEqual(rota[0], a)
                    self.assertEqual(rota[-1], b)

    def test_plano_reserva_retorno_e_pula_inviavel(self):
        ranking = [dict(escada_id='inviavel', estacao='C', criticidade=9, servico_min=100),
                   dict(escada_id='ok', estacao='A', criticidade=8, servico_min=10),
                   dict(escada_id='outra', estacao='C', criticidade=7, servico_min=10)]
        planejar = criar_planejador(self.g, ranking)
        p = planejar('B', .5)
        self.assertEqual([a['escada_id'] for a in p['atendimentos']], ['ok', 'outra'])
        self.assertEqual(p['total_min'], 28)
        self.assertEqual(p['rota_retorno'], ['C', 'A', 'B'])
        self.assertEqual(p['nao_atendidas'], ['inviavel'])
        self.assertEqual(planejar('B', 0)['atendimentos'], [])
        with self.assertRaises(ValueError):
            planejar('B', -1)

    def test_pesos_invalidos(self):
        for peso in [-1, 0, math.nan, math.inf]:
            with self.assertRaises(ValueError):
                montar_grafo(['A', 'B'], [('A', 'B', peso)])

    def test_integracao_sensorial_e_lacuna(self):
        leituras = pd.DataFrame({'escada_id': ['E1']*3,
            'timestamp': ['2026-01-01T00:00Z', '2026-01-01T01:00Z', '2026-01-01T02:00Z'],
            **{s: [0, 2, 4] for s in SENSORES}})
        config = {s: dict(referencia=0, escala=2, peso=1, sentido='alto') for s in SENSORES}
        resultado = incrementos_sensores(leituras, config, 1)
        self.assertEqual(resultado.incremento.tolist(), [0, .5, 1.5])
        with self.assertRaises(ValueError):
            incrementos_sensores(leituras, config, .5)


if __name__ == '__main__':
    unittest.main()
