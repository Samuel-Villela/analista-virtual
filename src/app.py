"""
app.py

Interface de chat da Fase 1 ("Chat de Dados") do Analista Virtual,
construída com Streamlit.

Fluxo:
1. O usuário pode enviar um CSV de vendas, ou o app usa o dataset de
   exemplo em data/vendas.csv
2. Os KPIs são calculados e exibidos na barra lateral
3. Um resumo executivo é gerado automaticamente ao carregar o dataset
4. O usuário continua a conversa fazendo perguntas em linguagem
   natural, com memória das mensagens trocadas na sessão atual

Execução: streamlit run src/app.py
"""

from pathlib import Path

import streamlit as st

from ai_client import AIProviderError, get_ai_provider
from analytics import DatasetError, carregar_dados, carregar_dados_de_arquivo, gerar_resumo
from config import get_settings
from conversation import construir_mensagens, montar_pedido_resumo_inicial
from evidence import gerar_evidencias

CAMINHO_CSV_PADRAO = Path(__file__).resolve().parent.parent / "data" / "vendas.csv"

st.set_page_config(page_title="Analista Virtual", page_icon="📊", layout="wide")


def _inicializar_estado() -> None:
    """Garante que as chaves usadas no session_state existam antes de serem lidas."""
    estado_padrao = {
        "historico": [],        # mensagens da conversa (memória), sem a de sistema
        "arquivo_atual": None,  # identifica o dataset carregado, para detectar troca
        "provider": None,       # instância do provedor de IA, criada uma vez por sessão
    }
    for chave, valor in estado_padrao.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def _obter_provider():
    """Cria o provedor de IA configurado uma única vez por sessão e reaproveita."""
    if st.session_state["provider"] is None:
        st.session_state["provider"] = get_ai_provider(get_settings())
    return st.session_state["provider"]


def _identificador_arquivo(arquivo_enviado) -> str:
    """Gera um identificador simples para detectar se o usuário trocou o dataset."""
    if arquivo_enviado is None:
        return "dataset_padrao"
    return f"{arquivo_enviado.name}:{arquivo_enviado.size}"


def _carregar_dataset(arquivo_enviado):
    """Carrega o dataset enviado pelo usuário ou, na ausência, o dataset de exemplo."""
    if arquivo_enviado is not None:
        return carregar_dados_de_arquivo(arquivo_enviado)
    return carregar_dados(str(CAMINHO_CSV_PADRAO))


def main() -> None:
    _inicializar_estado()

    st.title("Analista Virtual")
    st.caption("Converse com seus dados de vendas em linguagem natural.")

    with st.sidebar:
        st.header("📁 Dataset")
        arquivo_enviado = st.file_uploader(
            "Envie um CSV de vendas (opcional)",
            type="csv",
            help="Colunas esperadas: data, regiao, produto, vendas, lucro",
        )

    try:
        df = _carregar_dataset(arquivo_enviado)
    except DatasetError as erro:
        st.error(f"Não foi possível carregar o dataset: {erro}")
        st.stop()

    resumo = gerar_resumo(df)
    evidencias = gerar_evidencias(df)

    # Se o dataset mudou (novo upload), a conversa anterior perde sentido
    # — começamos um novo histórico para não misturar contextos diferentes.
    identificador_atual = _identificador_arquivo(arquivo_enviado)
    if identificador_atual != st.session_state["arquivo_atual"]:
        st.session_state["arquivo_atual"] = identificador_atual
        st.session_state["historico"] = []

    with st.sidebar:
        st.header("Indicadores")
        st.metric("Receita total:", f"R$ {resumo.receita_total:,.2f}")
        st.metric("Lucro total:", f"R$ {resumo.lucro_total:,.2f}")
        st.metric("Produto mais vendido:", resumo.produto_mais_vendido)
        st.metric("Região líder:", resumo.regiao_maior_faturamento)
        st.caption(f"{resumo.total_registros} registros carregados")

        st.divider()
        if st.button("🔄 Nova conversa"):
            st.session_state["historico"] = []
            st.rerun()

    try:
        provider = _obter_provider()
    except ValueError as erro:
        st.error(f"Configuração inválida: {erro}")
        st.stop()

    # Resumo automático: gerado apenas quando ainda não há histórico
    # (primeira execução da sessão ou dataset recém-carregado).
    if not st.session_state["historico"]:
        with st.spinner("Gerando resumo executivo..."):
            try:
                mensagens_resumo = construir_mensagens(
                    evidencias, historico=[], pergunta=montar_pedido_resumo_inicial()
                )
                resumo_texto = provider.gerar_resposta(mensagens_resumo)
                st.session_state["historico"].append(
                    {"role": "assistant", "content": resumo_texto}
                )
            except AIProviderError as erro:
                st.error(f"Não foi possível gerar o resumo automático: {erro}")

    for mensagem in st.session_state["historico"]:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    pergunta = st.chat_input("Pergunte algo sobre os dados...")

    if pergunta:
        st.session_state["historico"].append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        mensagens = construir_mensagens(
            evidencias,
            historico=st.session_state["historico"][:-1],
            pergunta=pergunta,
        )

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    resposta = provider.gerar_resposta(mensagens)
                except AIProviderError as erro:
                    resposta = f"❌ Não foi possível responder: {erro}"
            st.markdown(resposta)

        st.session_state["historico"].append({"role": "assistant", "content": resposta})


if __name__ == "__main__":
    main()
