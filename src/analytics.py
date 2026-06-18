"""
analytics.py

Responsável por carregar o dataset de vendas e calcular as métricas
de negócio (KPIs) que serão exibidas ao usuário e enviadas para a IA.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


class DatasetError(Exception):
    """Erro lançado quando o CSV não pode ser lido ou está mal formatado."""


@dataclass(frozen=True)
class ResumoVendas:
    """Estrutura que agrupa os indicadores calculados a partir do dataset."""

    receita_total: float
    lucro_total: float
    produto_mais_vendido: str
    regiao_maior_faturamento: str
    total_registros: int


COLUNAS_OBRIGATORIAS = {"data", "regiao", "produto", "vendas", "lucro"}


def _ler_csv(origem) -> pd.DataFrame:
    """
    Lê um CSV a partir de qualquer origem aceita pelo pandas: um caminho
    (str/Path) ou um objeto tipo arquivo, como o retorno de
    st.file_uploader no Streamlit.
    """
    try:
        return pd.read_csv(origem)
    except pd.errors.EmptyDataError as exc:
        raise DatasetError("O arquivo CSV está vazio.") from exc
    except pd.errors.ParserError as exc:
        raise DatasetError("O arquivo CSV está mal formatado.") from exc


def _validar_dataframe(df: pd.DataFrame) -> None:
    """Garante que o DataFrame tenha as colunas obrigatórias e não esteja vazio."""
    colunas_faltantes = COLUNAS_OBRIGATORIAS - set(df.columns)
    if colunas_faltantes:
        raise DatasetError(
            f"Colunas obrigatórias ausentes no CSV: {sorted(colunas_faltantes)}"
        )

    if df.empty:
        raise DatasetError("O dataset não contém nenhum registro.")


def carregar_dados(caminho_csv: str) -> pd.DataFrame:
    """
    (Fase 0) Lê o arquivo CSV de vendas a partir de um caminho no disco
    e retorna um DataFrame validado.

    Levanta DatasetError caso o arquivo não exista, esteja vazio,
    ou não contenha as colunas obrigatórias.
    """
    path = Path(caminho_csv)

    if not path.exists():
        raise DatasetError(f"Arquivo não encontrado: {caminho_csv}")

    df = _ler_csv(path)
    _validar_dataframe(df)
    return df


def carregar_dados_de_arquivo(arquivo) -> pd.DataFrame:
    """
    (Fase 1) Lê o arquivo CSV de vendas a partir de um objeto tipo
    arquivo — por exemplo, o retorno de st.file_uploader no Streamlit —
    e retorna um DataFrame validado.

    Usa a mesma validação de carregar_dados(), garantindo que o
    comportamento (colunas obrigatórias, dataset vazio) seja idêntico
    independentemente de o CSV vir do disco ou de um upload.
    """
    df = _ler_csv(arquivo)
    _validar_dataframe(df)
    return df


def calcular_receita_total(df: pd.DataFrame) -> float:
    """Soma a coluna 'vendas', representando a receita total."""
    return float(df["vendas"].sum())


def calcular_lucro_total(df: pd.DataFrame) -> float:
    """Soma a coluna 'lucro', representando o lucro total."""
    return float(df["lucro"].sum())


def calcular_produto_mais_vendido(df: pd.DataFrame) -> str:
    """Identifica o produto com maior volume de vendas somado."""
    return str(df.groupby("produto")["vendas"].sum().idxmax())


def calcular_regiao_maior_faturamento(df: pd.DataFrame) -> str:
    """Identifica a região com maior faturamento (soma de vendas)."""
    return str(df.groupby("regiao")["vendas"].sum().idxmax())


def calcular_total_registros(df: pd.DataFrame) -> int:
    """Retorna a quantidade total de linhas (registros) do dataset."""
    return int(len(df))


def gerar_resumo(df: pd.DataFrame) -> ResumoVendas:
    """Calcula todos os KPIs de uma vez e retorna um objeto ResumoVendas."""
    return ResumoVendas(
        receita_total=calcular_receita_total(df),
        lucro_total=calcular_lucro_total(df),
        produto_mais_vendido=calcular_produto_mais_vendido(df),
        regiao_maior_faturamento=calcular_regiao_maior_faturamento(df),
        total_registros=calcular_total_registros(df),
    )
