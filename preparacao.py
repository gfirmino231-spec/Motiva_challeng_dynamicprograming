"""Leitura auditável do histórico oficial; não cria leituras de sensores."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA_ANALISE = pd.Timestamp('2026-10-18 23:59:59')

def carregar():
    """Lê sete campos necessários e assinatura para manter a deduplicação original."""
    caminho = ROOT / 'dados/historico_avarias.csv'
    return pd.read_csv(caminho, dtype=object), caminho

def preparar(bruto):
    """Preserva extremos; remove apenas cópias exatas e audita datas inválidas.

    Duração negativa ou sem data fica ausente. Eventos com mesmo início/fim
    são mantidos (duração zero). Não interpreta ausência de X como falso certo.
    """
    df = bruto.copy()
    df.columns = df.columns.str.strip()
    for coluna in df:
        df[coluna] = df[coluna].map(lambda x: x.strip() if isinstance(x, str) else x)
        df[coluna] = df[coluna].replace('', np.nan)
    duplicadas = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()
    def instante(data, hora):
        datas = pd.to_datetime(df[data], dayfirst=True, errors='coerce')
        # Horas Excel chegam como datetime.time; datas ausentes não são inferidas.
        horas = pd.to_timedelta(df[hora].astype('string'), errors='coerce')
        return datas.dt.normalize() + horas
    df['inicio'] = instante('Início avaria', 'Hora início avaria')
    df['fim'] = instante('Fim da avaria', 'Hora do fim da avaria')
    df['duracao_bruta_min'] = (df['fim'] - df['inicio']).dt.total_seconds() / 60
    df['data_futura'] = (df['inicio'] > DATA_ANALISE) | (df['fim'] > DATA_ANALISE)
    df['duracao_min'] = df['duracao_bruta_min'].where((df['duracao_bruta_min'] >= 0) & ~df['data_futura'])
    df['escada_id'] = df['Local de Instalação'].astype('string')
    df['codigo_estacao'] = df['escada_id'].str.extract(r'-ECR-([^-]+)(?:-|$)', expand=False)
    df['equipamento_identificado'] = df['escada_id'].str.contains(r'-ECR-[^-]+-ER\d+$', na=False)
    df['ano'] = df['inicio'].dt.year.astype('Int64')
    df['mes'] = df['inicio'].dt.to_period('M').astype('string')
    auditoria = dict(linhas_originais=len(bruto), duplicatas_exatas=duplicadas,
                     linhas_preparadas=len(df), inicio_ausente=int(df.inicio.isna().sum()),
                     fim_ausente=int(df.fim.isna().sum()),
                     duracao_negativa=int((df.duracao_bruta_min < 0).sum()),
                     data_futura=int(df.data_futura.sum()),
                     duracao_valida=int(df.duracao_min.notna().sum()),
                     equipamento_ausente=int(df.escada_id.isna().sum()))
    return df, auditoria
