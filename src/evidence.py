"""
evidence.py

Camada de "evidências estruturadas": transforma os KPIs calculados pelo
motor analítico (analytics.py) em um pacote de contexto pronto para ser
injetado no prompt da IA.

Por que essa camada existe
---------------------------
Ela isola o motor analítico do motor de conversa. Hoje (Fase 1), o
pacote de evidências contém apenas os KPIs básicos (receita, lucro,
produto mais vendido, região líder). Na Fase 2 ("Motor Analítico"), as
mesmas evidências serão enriquecidas com rankings, comparações
temporais (MoM/YoY) e tendências — bastando preencher o campo `achados`
abaixo. Nem `conversation.py` nem `app.py` precisam ser alterados,
porque ambos dependem apenas do método `.como_texto()`.

Como evoluir para a Fase 2
---------------------------
1. Criar em analytics.py as novas funções analíticas, por exemplo:
   calcular_variacao_mom(df), calcular_variacao_yoy(df),
   ranking_produtos(df), ranking_regioes(df), detectar_tendencias(df).
2. Em gerar_evidencias() (abaixo), chamar essas funções e transformar
   cada achado relevante em uma string curta, adicionando-a à lista
   `achados` (ex: "Receita caiu 12% em relação ao mês anterior").
3. Nada mais precisa mudar — o texto formado por `.como_texto()` já é
   automaticamente incluído no prompt enviado à IA a cada turno da
   conversa, via conversation.montar_instrucao_sistema().
"""

from dataclasses import dataclass, field

import pandas as pd

from analytics import ResumoVendas, gerar_resumo
from formatting import formatar_indicadores


@dataclass
class Evidencias:
    """
    Pacote estruturado de evidências sobre o dataset atualmente carregado.

    Atributos:
        resumo: os KPIs básicos calculados pelo motor analítico (Fase 1).
        achados: observações textuais já formatadas e prontas para
            exibição (ex: "Nordeste cresceu 18% no período"). Vazia na
            Fase 1; é o ponto de extensão da Fase 2.
    """

    resumo: ResumoVendas
    achados: list[str] = field(default_factory=list)

    def como_texto(self) -> str:
        """Formata o pacote de evidências como um bloco de texto único."""
        blocos = [formatar_indicadores(self.resumo)]

        if self.achados:
            pontos = "\n".join(f"- {achado}" for achado in self.achados)
            blocos.append(f"Pontos de atenção identificados:\n{pontos}")

        return "\n\n".join(blocos)


def gerar_evidencias(df: pd.DataFrame) -> Evidencias:
    """
    Gera o pacote de evidências a partir do DataFrame carregado.

    Hoje (Fase 1) delega inteiramente para analytics.gerar_resumo().
    Na Fase 2, esta função passará a chamar também as novas funções do
    motor analítico e a popular `achados` com os resultados.
    """
    return Evidencias(resumo=gerar_resumo(df))
