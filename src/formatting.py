"""
formatting.py

Funções de apresentação: transformam os indicadores calculados em texto
legível, tanto para exibição no terminal quanto para compor os prompts
enviados à IA. Mantém a formatação separada do cálculo (analytics.py) e
da orquestração (main.py).
"""

from analytics import ResumoVendas


def formatar_moeda(valor: float) -> str:
    """Formata um número como moeda em reais (ex: R$ 12.345,67)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_indicadores(resumo: ResumoVendas) -> str:
    """Formata os indicadores calculados como um bloco de texto único."""
    return (
        f"Receita total: {formatar_moeda(resumo.receita_total)}\n"
        f"Lucro total: {formatar_moeda(resumo.lucro_total)}\n"
        f"Produto mais vendido: {resumo.produto_mais_vendido}\n"
        f"Região líder: {resumo.regiao_maior_faturamento}\n"
        f"Total de registros: {resumo.total_registros}"
    )


def exibir_resumo(resumo: ResumoVendas) -> None:
    """Imprime os KPIs calculados de forma legível no terminal."""
    print("\n📊 Indicadores de Vendas")
    print("-" * 40)
    print(formatar_indicadores(resumo))
    print("-" * 40)
