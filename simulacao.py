"""Dados artificiais para demonstração acadêmica; não são medições da Motiva."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SENSORES = ['vibracao', 'temperatura', 'corrente', 'tensao', 'nivel_oleo', 'velocidade']
UNIDADES = ['mm/s (hipótese)', '°C', 'A', 'V', '% (hipótese)', 'm/s']

def gerar():
    """Gera 22 escadas fictícias × 96 leituras, semente 566903."""
    rng = np.random.default_rng(566903)
    estacoes = ['VSO','MBI','BUT','PIN','FAL','FRA','FRE','PTA','HIG','REP','LUZ']
    linhas = []
    for i, estacao in enumerate(estacoes):
        for escada in [1, 2]:
            gravidade = (i + escada) / 12
            for t, instante in enumerate(pd.date_range('2026-09-01', periods=96, freq='15min', tz='UTC')):
                carga = 0.5 + 0.35 * np.sin(2*np.pi*t/96) + rng.normal(0, .04)
                desgaste = gravidade * t / 95
                pico = 1.8 if i == 8 and escada == 2 and t in [70, 71] else 0
                linhas.append(dict(escada_id=f'SIM-{estacao}-ER{escada:02}', estacao=estacao,
                    timestamp=instante.isoformat(), origem='SIMULADO',
                    condicao='carga_alta' if carga > .6 else 'carga_baixa',
                    vibracao=max(.1, 1.2+1.8*desgaste+.7*carga+pico+rng.normal(0,.12)),
                    temperatura=40+10*carga+14*desgaste+4*pico+rng.normal(0,.8),
                    corrente=8+5*carga+3*desgaste+rng.normal(0,.3),
                    tensao=380-2*carga+rng.normal(0,1.5),
                    nivel_oleo=85-18*desgaste+rng.normal(0,.6),
                    velocidade=.5-.025*desgaste-.01*pico+rng.normal(0,.002)))
    completo = pd.DataFrame(linhas)
    bruto = completo.copy()
    bruto.loc[[20, 130, 800], 'temperatura'] = np.nan
    bruto = pd.concat([bruto, bruto.iloc[[10, 100]]], ignore_index=True)
    pasta = ROOT / 'dados'; pasta.mkdir(exist_ok=True)
    completo.to_csv(pasta / 'sensores_simulados.csv', index=False)
    bruto.to_csv(pasta / 'sensores_simulados_brutos.csv', index=False)
    config = {
        'vibracao': dict(referencia=2, escala=1, peso=2, sentido='alto'),
        'temperatura': dict(referencia=50, escala=10, peso=1, sentido='alto'),
        'corrente': dict(referencia=11, escala=4, peso=1, sentido='alto'),
        'tensao': dict(referencia=380, escala=10, peso=1, sentido='bilateral'),
        'nivel_oleo': dict(referencia=80, escala=20, peso=1, sentido='baixo'),
        'velocidade': dict(referencia=.5, escala=.05, peso=1, sentido='bilateral')}
    (pasta / 'parametros_sensores_simulados.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    (pasta / 'LEIA_ME_SIMULACAO.md').write_text(
        '# DADOS SIMULADOS — SEM ORIGEM NA MOTIVA\n\n'
        'Gerados por simulacao.py, semente 566903: 22 equipamentos fictícios, 96 leituras de 15 minutos cada. '
        'Carga e tendência de desgaste foram inseridas nas equações para produzir relações didáticas. '
        'As correlações resultantes decorrem dessa construção e não validam fenômenos físicos. '
        'A versão bruta contém duas duplicatas e três temperaturas ausentes, inseridas intencionalmente. '
        'São fornecidas também as leituras completas antes desses defeitos. '
        'Unidades, referências, escalas, pesos e limites são hipóteses de demonstração, sem calibração técnica. '
        'Não concatenar estes arquivos com dados reais.\n', encoding='utf-8')
    print('Simulação criada:', len(completo), 'leituras completas;', len(bruto), 'linhas brutas.')

def preparar():
    """Limpa somente a simulação; interpola três lacunas internas isoladas."""
    bruto = pd.read_csv(ROOT / 'dados/sensores_simulados_brutos.csv')
    df = bruto.drop_duplicates().sort_values(['escada_id', 'timestamp']).reset_index(drop=True)
    df['timestamp'] = pd.to_datetime(df.timestamp, utc=True)
    faltantes = int(df[SENSORES].isna().sum().sum())
    for sensor in SENSORES:
        df[sensor] = df.groupby('escada_id')[sensor].transform(
            lambda s: s.interpolate(limit=1, limit_area='inside'))
    if df[SENSORES].isna().any().any():
        raise ValueError('Há lacunas não resolvidas na simulação')
    return bruto, df, dict(duplicatas=len(bruto)-len(df), valores_interpolados=faltantes)

if __name__ == '__main__':
    gerar()
