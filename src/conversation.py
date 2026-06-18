"""
conversation.py

Monta as mensagens enviadas ao provedor de IA a cada turno da conversa,
combinando:
- uma instrução de sistema (papel do assistente + evidências atuais)
- o histórico de mensagens já trocadas na sessão (memória da conversa)
- a nova pergunta do usuário

A instrução de sistema é reconstruída em TODO turno a partir das
evidências atuais — isso garante que, se o dataset mudar (novo upload)
ou se a Fase 2 enriquecer as evidências com novos achados, a IA sempre
responde com base no contexto mais recente, sem depender de um system
prompt "congelado" no início da conversa.
"""

from evidence import Evidencias

# Uma mensagem segue o formato {"role": "system"|"user"|"assistant", "content": str}
Mensagem = dict[str, str]

# Quantidade máxima de turnos (pergunta + resposta) mantidos no histórico
# enviado à IA como contexto. Turnos mais antigos continuam visíveis na
# tela (responsabilidade de app.py), mas saem do que é enviado ao
# modelo, evitando que a conversa exceda a janela de contexto.
MAX_TURNOS_HISTORICO = 10

INSTRUCAO_BASE = (
    "Você é o Analista Virtual, um assistente de negócios que responde "
    "perguntas sobre um dataset de vendas. Responda em português, de "
    "forma direta e objetiva. Sempre baseie suas respostas nas "
    "evidências fornecidas abaixo; se a pergunta não puder ser "
    "respondida apenas com esses dados, diga isso claramente em vez de "
    "inventar uma resposta."
)


def montar_instrucao_sistema(evidencias: Evidencias) -> str:
    """Monta a mensagem de sistema com o papel do assistente e as evidências atuais."""
    return f"{INSTRUCAO_BASE}\n\nEvidências disponíveis:\n{evidencias.como_texto()}"


def montar_pedido_resumo_inicial() -> str:
    """Pergunta padrão usada para gerar o resumo automático ao carregar um dataset."""
    return (
        "Apresente um resumo executivo dos destaques desses dados em até "
        "5 tópicos curtos."
    )


def construir_mensagens(
    evidencias: Evidencias,
    historico: list[Mensagem],
    pergunta: str,
) -> list[Mensagem]:
    """
    Monta a lista completa de mensagens enviada ao provedor de IA:
    [sistema, ...histórico recente..., pergunta atual]

    `historico` deve conter apenas mensagens com role "user" ou
    "assistant" (sem a mensagem de sistema, que é sempre recalculada
    aqui a partir das evidências atuais).
    """
    sistema: Mensagem = {"role": "system", "content": montar_instrucao_sistema(evidencias)}
    historico_recente = historico[-(MAX_TURNOS_HISTORICO * 2):]
    pergunta_atual: Mensagem = {"role": "user", "content": pergunta}

    return [sistema, *historico_recente, pergunta_atual]
