"""Ponto de integração para o dataset de sensores, ainda não fornecido.

Não utiliza o histórico de avarias como se fossem leituras físicas.
Referências, escalas e pesos devem ser fornecidos e validados pela engenharia.
"""
import numpy as np
import pandas as pd

SENSORES = ('vibracao', 'temperatura', 'corrente', 'tensao', 'nivel_oleo', 'velocidade')

def incrementos_sensores(leituras, configuracao, max_intervalo_horas):
    """Produz exposição acumulável por escada, com integração trapezoidal.

    Entradas: DataFrame com escada_id, timestamp e SENSORES; configuração de cada
    sinal com referencia, escala positiva, peso não negativo e sentido ('alto',
    'baixo', 'bilateral'). Índice = média ponderada de desvios normalizados.
    Incremento = média dos índices consecutivos × intervalo em horas.
    Primeira leitura contribui zero; lacunas acima do limite causam erro, pois
    não se conhece a condição durante o intervalo. Não estima dano físico.
    """
    exigidas = {'escada_id', 'timestamp', *SENSORES}
    if not exigidas.issubset(leituras.columns):
        raise ValueError(f'Colunas ausentes: {sorted(exigidas - set(leituras.columns))}')
    if not np.isfinite(max_intervalo_horas) or max_intervalo_horas <= 0:
        raise ValueError('Limite de intervalo deve ser positivo e finito')
    df = leituras.copy()
    if df.escada_id.isna().any():
        raise ValueError('Equipamento ausente')
    df['timestamp'] = pd.to_datetime(df.timestamp, errors='raise', utc=True)
    if df.timestamp.isna().any() or df.duplicated(['escada_id', 'timestamp']).any():
        raise ValueError('Timestamp ausente ou duplicado')
    df = df.sort_values(['escada_id', 'timestamp']).reset_index(drop=True)
    pesos, total = 0.0, np.zeros(len(df))
    for sensor in SENSORES:
        cfg = configuracao[sensor]
        ref, escala, peso = (float(cfg[k]) for k in ('referencia', 'escala', 'peso'))
        if not all(np.isfinite([ref, escala, peso])) or escala <= 0 or peso < 0:
            raise ValueError('Referência, escala ou peso inválido')
        valores = pd.to_numeric(df[sensor], errors='raise').to_numpy(dtype=float)
        if not np.isfinite(valores).all():
            raise ValueError(f'Leitura ausente/infinita: {sensor}')
        delta = (valores - ref) / escala
        sentido = cfg['sentido']
        if sentido == 'alto':
            sinal = np.maximum(delta, 0)
        elif sentido == 'baixo':
            sinal = np.maximum(-delta, 0)
        elif sentido == 'bilateral':
            sinal = np.abs(delta)
        else:
            raise ValueError('Sentido desconhecido')
        total += peso * sinal
        pesos += peso
    if pesos <= 0:
        raise ValueError('Soma dos pesos deve ser positiva')
    df['indice'] = total / pesos
    intervalo = df.groupby('escada_id').timestamp.diff().dt.total_seconds().div(3600).fillna(0)
    if (intervalo > max_intervalo_horas).any():
        raise ValueError('Lacuna temporal excede limite; revisar antes de integrar')
    anterior = df.groupby('escada_id').indice.shift().fillna(df.indice)
    df['incremento'] = (anterior + df.indice) / 2 * intervalo
    return df
