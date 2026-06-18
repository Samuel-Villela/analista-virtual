
## Pré-requisitos

- Python 3.10+
- [Ollama](https://ollama.com) instalado e em execução
- Modelo `gemma3:1b` baixado:

```bash
ollama pull gemma3:1b
```

## Instalação

```bash
cd analista_virtual
pip install -r requirements.txt
```

## Configuração (.env)

O arquivo `.env` já vem com valores padrão prontos para uso local:

```env
AI_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
```

- `AI_PROVIDER`: define qual provedor de IA será usado (`ollama` nesta versão)
- `OLLAMA_HOST`: endereço do servidor Ollama
- `OLLAMA_MODEL`: modelo que será utilizado para gerar as análises

## Como executar

1. Garanta que o Ollama está rodando:

```bash
ollama serve
```

2. Em outro terminal, execute a aplicação:

```bash
python src/main.py
```

O sistema irá:

1. Ler o CSV em `data/vendas.csv`
2. Calcular receita total, lucro total, produto mais vendido, região com
   maior faturamento e total de registros
3. Exibir os indicadores no terminal
4. Enviar um resumo executivo para o Ollama e exibir a análise gerada
5. Abrir o **modo de perguntas**: você pode digitar perguntas simples
   sobre os dados (ex: "qual produto vendeu mais?") e o assistente
   responde com base nos indicadores já calculados. Digite `sair`,
   `exit` ou `quit` para encerrar.

> **Nota:** nesta versão (Fase 0) cada pergunta é respondida de forma
> independente — não há memória entre uma pergunta e outra. Para
> conversas com memória completa, use a interface da Fase 1 abaixo.

## Como executar (Fase 1 — Streamlit)

```bash
streamlit run src/app.py
```

O navegador abre automaticamente em `http://localhost:8501`. A interface:

1. Usa o dataset de exemplo (`data/vendas.csv`) até que você envie outro
   CSV pela barra lateral
2. Exibe os KPIs como métricas na barra lateral, atualizadas a cada
   novo arquivo enviado
3. Gera automaticamente um resumo executivo ao carregar o dataset
4. Permite continuar a conversa pela caixa de chat — as perguntas
   seguintes levam em conta tudo o que já foi perguntado na sessão
   (memória da conversa)
5. O botão **"🔄 Nova conversa"** limpa o histórico sem precisar
   recarregar a página; enviar um CSV diferente também reinicia a
   conversa automaticamente, para não misturar contextos de datasets
   diferentes

> A memória da conversa vive em `st.session_state` — ou seja, dura
> enquanto a aba do navegador estiver aberta. Persistência entre
> sessões (banco de dados, arquivo, etc.) não faz parte do roadmap
> desta fase.

## Dataset esperado

O CSV deve conter as colunas:

```
data,regiao,produto,vendas,lucro
```

## Tratamento de erros

- CSV ausente, vazio ou com colunas faltando: mensagem clara indicando o
  problema, sem travar a aplicação.
- Ollama não está rodando: a aplicação orienta a executar `ollama serve`
  e baixar o modelo com `ollama pull gemma3:1b`.
- Timeout (modelo demorando a responder): mensagem específica explicando
  que modelos locais em CPU podem ser mais lentos.

## Status do Roadmap

- ✅ Fase 0 — Prova de Conceito (terminal)
- ✅ Fase 1 — Chat de Dados (Streamlit, upload de CSV, memória de conversa)
- ⏳ Fase 2 — Motor Analítico (rankings, MoM/YoY, tendências) — próxima
- ⏳ Fase 3 — Insights automáticos e proativos
- ⏳ Fase 4 — Integração com Power BI
- ⏳ Fase 5 — Relatórios executivos automatizados
