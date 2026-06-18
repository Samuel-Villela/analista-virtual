"""
chat.py

Modo de perguntas e respostas pós-resumo — item "Respostas a perguntas
simples" da Fase 0 do roadmap.

Permite ao usuário continuar interagindo com os dados já carregados,
fazendo perguntas em linguagem natural diretamente no terminal. Cada
pergunta é respondida de forma independente, sempre reancorada nos KPIs
já calculados (não há nova leitura do CSV nem chamadas extras ao Pandas).

Importante: esta versão NÃO mantém histórico de conversa — cada pergunta
é enviada isoladamente ao modelo, junto com os indicadores. Histórico de
conversa, memória entre mensagens e interface dedicada de chat ficam para
a Fase 1 (Chat de Dados), que evolui este módulo.
"""

from ai_client import AIProvider, AIProviderError
from analytics import ResumoVendas
from formatting import formatar_indicadores

COMANDOS_SAIDA = {"sair", "exit", "quit"}

INSTRUCAO_BASE = (
    "Você é um analista de negócios. Responda em português, de forma "
    "direta e objetiva, sem usar markdown."
)


def montar_prompt_inicial(resumo: ResumoVendas) -> str:
    """Monta o prompt do resumo executivo inicial."""
    return (
        f"{INSTRUCAO_BASE}\n\n"
        f"{formatar_indicadores(resumo)}\n\n"
        "Explique os principais destaques desses resultados em até 5 "
        "tópicos curtos."
    )


def montar_prompt_pergunta(resumo: ResumoVendas, pergunta: str) -> str:
    """Monta o prompt para uma pergunta de acompanhamento do usuário."""
    return (
        f"{INSTRUCAO_BASE}\n\n"
        "Contexto - indicadores calculados a partir do dataset de vendas:\n"
        f"{formatar_indicadores(resumo)}\n\n"
        f"Pergunta do usuário: {pergunta}\n\n"
        "Responda apenas com base nesses indicadores. Se a pergunta não "
        "puder ser respondida apenas com esses dados, explique isso "
        "claramente em vez de inventar uma resposta."
    )


def iniciar_modo_perguntas(provider: AIProvider, resumo: ResumoVendas) -> None:
    """
    Inicia um loop interativo no terminal onde o usuário pode fazer
    perguntas simples sobre os dados já carregados.

    Encerra com 'sair', 'exit', 'quit', linha vazia + Ctrl+D, ou Ctrl+C.
    """
    print("\n💬 Modo de perguntas — digite 'sair' para encerrar\n")

    while True:
        try:
            pergunta = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando o modo de perguntas.")
            break

        if not pergunta:
            continue

        if pergunta.lower() in COMANDOS_SAIDA:
            print("Encerrando o modo de perguntas.")
            break

        try:
            resposta = provider.gerar_analise(montar_prompt_pergunta(resumo, pergunta))
        except AIProviderError as erro:
            print(f"❌ Não foi possível responder: {erro}\n")
            continue

        print(f"\nAnalista Virtual: {resposta}\n")
