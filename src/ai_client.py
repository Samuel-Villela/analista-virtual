"""
ai_client.py

Define a arquitetura desacoplada de provedores de IA.

A interface AIProvider garante que qualquer provedor (Ollama, OpenAI, etc.)
exponha o mesmo contrato: gerar_resposta(mensagens) -> str, recebendo uma
lista de mensagens no formato [{"role": ..., "content": ...}] — o mesmo
formato usado pelas APIs de chat da OpenAI e do Ollama. Isso permite
conversas com múltiplos turnos e memória (Fase 1), e deixa o projeto
pronto para novos provedores (ex: OpenAIProvider) sem alterar nenhum
código que consome essa interface.

Isso permite que main.py, chat.py e app.py nunca precisem saber qual
provedor está sendo usado por baixo dos panos — basta trocar AI_PROVIDER
no .env e a função fábrica get_ai_provider() devolve a implementação
correta.
"""

from abc import ABC, abstractmethod

import requests

from config import Settings

# Uma mensagem segue o formato {"role": "system"|"user"|"assistant", "content": str}
Mensagem = dict[str, str]


class AIProviderError(Exception):
    """Erro genérico levantado quando um provedor de IA falha ao responder."""


class AIProvider(ABC):
    """
    Interface abstrata que todo provedor de IA deve implementar.

    Apenas `gerar_resposta` precisa ser implementado por uma subclasse.
    `gerar_analise` é mantido por compatibilidade com a Fase 0 (uso via
    terminal, sem histórico de conversa) e já vem implementado aqui como
    um atalho que envia uma única mensagem de usuário.
    """

    @abstractmethod
    def gerar_resposta(self, mensagens: list[Mensagem]) -> str:
        """Recebe o histórico de mensagens da conversa e retorna a resposta do modelo."""
        raise NotImplementedError

    def gerar_analise(self, prompt: str) -> str:
        """Atalho para enviar um único prompt sem histórico (uso da Fase 0)."""
        return self.gerar_resposta([{"role": "user", "content": prompt}])


class OllamaProvider(AIProvider):
    """
    Implementação concreta de AIProvider que utiliza um modelo local via
    Ollama através do endpoint de chat da API REST (/api/chat), que
    aceita uma lista de mensagens com papéis e mantém o modelo
    consciente do histórico da conversa.
    """

    # Modelos maiores (ex: Qwen3 4B) podem demorar bem mais que modelos
    # pequenos como gemma3:1b, principalmente em CPU; ajuste conforme o
    # hardware disponível.
    TIMEOUT_SEGUNDOS = 180
    # Qwen3 usa modo de raciocínio (thinking) por padrão e a documentação
    # oficial recomenda temperatura por volta de 0.6 nesse modo — valores
    # muito baixos (ex: 0.3, usado para gemma3:1b) podem gerar repetição.
    TEMPERATURA = 0.6

    def __init__(self, host: str, model: str) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.endpoint = f"{self.host}/api/chat"

    def _preparar_mensagens(self, mensagens: list[Mensagem]) -> list[Mensagem]:
        """
        Retorna uma cópia das mensagens, ajustada para peculiaridades do
        modelo configurado. Nunca modifica a lista original — ela
        continua sendo a fonte da verdade exibida na tela e armazenada
        na sessão.

        O Qwen3 ativa um modo de raciocínio (thinking) por padrão, que
        gera uma cadeia de pensamento antes da resposta final — isso
        aumenta bastante o tempo de geração para perguntas objetivas
        sobre KPIs já calculados. Anexar "/no_think" à última mensagem
        do usuário desativa esse modo. Outros modelos (ex: gemma3) não
        reconhecem essa tag e a ignoram.
        """
        copia = [dict(mensagem) for mensagem in mensagens]

        if "qwen3" in self.model.lower() and copia and copia[-1]["role"] == "user":
            copia[-1]["content"] = f"{copia[-1]['content']}\n\n/no_think"

        return copia

    def gerar_resposta(self, mensagens: list[Mensagem]) -> str:
        """
        Envia o histórico de mensagens ao Ollama e retorna a resposta
        gerada pelo modelo.

        Trata separadamente:
        - Erro de conexão (Ollama não está rodando)
        - Timeout (modelo demorando demais para responder)
        - Outros erros HTTP/inesperados
        """
        payload = {
            "model": self.model,
            "messages": self._preparar_mensagens(mensagens),
            "stream": False,
            "options": {
                "temperature": self.TEMPERATURA,
            },
        }

        try:
            resposta = requests.post(
                self.endpoint,
                json=payload,
                timeout=self.TIMEOUT_SEGUNDOS,
            )
            resposta.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise AIProviderError(
                "Não foi possível conectar ao Ollama em "
                f"'{self.host}'.\n"
                "Verifique se o servidor está rodando com o comando: ollama serve\n"
                f"E se o modelo foi baixado com: ollama pull {self.model}"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise AIProviderError(
                f"O Ollama demorou mais de {self.TIMEOUT_SEGUNDOS}s para responder.\n"
                "O modelo pode estar demorando para carregar ou processar o "
                "pedido. Tente novamente ou utilize um modelo menor."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise AIProviderError(
                f"O Ollama retornou um erro HTTP: {exc}\n"
                f"Verifique se o modelo '{self.model}' foi baixado com: "
                f"ollama pull {self.model}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise AIProviderError(f"Erro inesperado ao chamar o Ollama: {exc}") from exc

        try:
            dados = resposta.json()
        except ValueError as exc:
            raise AIProviderError(
                "O Ollama retornou uma resposta em formato inesperado."
            ) from exc

        texto = dados.get("message", {}).get("content", "").strip()
        if not texto:
            raise AIProviderError(
                "O Ollama retornou uma resposta vazia. "
                f"Verifique se o modelo '{self.model}' está funcionando corretamente."
            )

        return texto


def get_ai_provider(settings: Settings) -> AIProvider:
    """
    Função fábrica: lê settings.ai_provider e devolve a implementação
    correta de AIProvider.

    Hoje suporta apenas "ollama". No futuro, basta adicionar um novo
    `elif settings.ai_provider == "openai": return OpenAIProvider(...)`
    sem alterar nenhum outro arquivo do projeto.
    """
    if settings.ai_provider == "ollama":
        return OllamaProvider(host=settings.ollama_host, model=settings.ollama_model)

    raise ValueError(
        f"Provedor de IA '{settings.ai_provider}' não suportado nesta versão. "
        "Provedores disponíveis: ollama."
    )
