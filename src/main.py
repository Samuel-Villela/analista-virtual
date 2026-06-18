"""
main.py

Ponto de entrada da aplicação "Analista Virtual" (Versão 0A).

Fluxo:
1. Lê o CSV de vendas
2. Calcula os KPIs com Pandas
3. Exibe os indicadores no terminal
4. Monta um prompt executivo e solicita uma análise ao provedor de IA
   configurado (Ollama por padrão)
5. Exibe a análise gerada
6. Abre o modo de perguntas, permitindo o usuário continuar interagindo
   com os dados em linguagem natural (sem histórico de conversa)
"""

import sys
from pathlib import Path

from ai_client import AIProviderError, get_ai_provider
from analytics import DatasetError, carregar_dados, gerar_resumo
from chat import iniciar_modo_perguntas, montar_prompt_inicial
from config import get_settings
from formatting import exibir_resumo

CAMINHO_CSV = Path(__file__).resolve().parent.parent / "data" / "vendas.csv"


def main() -> None:
    settings = get_settings()

    # 1. Carregar e validar o dataset
    try:
        df = carregar_dados(str(CAMINHO_CSV))
    except DatasetError as erro:
        print(f"❌ Erro ao ler o dataset: {erro}")
        sys.exit(1)

    # 2. Calcular os KPIs
    resumo = gerar_resumo(df)

    # 3. Exibir os indicadores
    exibir_resumo(resumo)

    # 4. Solicitar análise ao provedor de IA configurado
    print(f"\n🤖 Gerando análise com o provedor '{settings.ai_provider}'...\n")

    try:
        provider = get_ai_provider(settings)
        analise = provider.gerar_analise(montar_prompt_inicial(resumo))
    except (AIProviderError, ValueError) as erro:
        print(f"❌ Não foi possível gerar a análise: {erro}")
        sys.exit(1)

    # 5. Exibir a análise gerada
    print("📝 Análise do Analista Virtual")
    print("-" * 40)
    print(analise)
    print("-" * 40)

    # 6. Modo de perguntas — continuação opcional da interação
    iniciar_modo_perguntas(provider, resumo)


if __name__ == "__main__":
    main()
