"""
config.py

Centraliza a leitura das variáveis de ambiente utilizadas pela aplicação.
Mantém a configuração de provedor de IA desacoplada do restante do código,
permitindo trocar o provedor (Ollama, OpenAI, etc.) apenas alterando o .env.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carrega as variáveis definidas no arquivo .env para o ambiente do processo
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Agrupa todas as configurações da aplicação em um único objeto."""

    ai_provider: str
    ollama_host: str
    ollama_model: str


def get_settings() -> Settings:
    """
    Lê as variáveis de ambiente e retorna um objeto Settings imutável.

    Variáveis suportadas:
        AI_PROVIDER  -> qual provedor de IA usar (padrão: "ollama")
        OLLAMA_HOST  -> endereço do servidor Ollama (padrão: http://localhost:11434)
        OLLAMA_MODEL -> modelo a ser utilizado no Ollama (padrão: gemma3:1b)
    """
    return Settings(
        ai_provider=os.getenv("AI_PROVIDER", "ollama").strip().lower(),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").strip(),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma3:1b").strip(),
    )
