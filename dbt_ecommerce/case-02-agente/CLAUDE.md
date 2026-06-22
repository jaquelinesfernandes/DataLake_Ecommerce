# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agente de Dados com Bot Telegram

LLM agent para e-commerce brasileiro com 3 capacidades:
1. **Chat livre** — Claude consulta o banco via tool use e responde qualquer pergunta analítica
2. **Relatório executivo** — 4 queries fixas nos Data Marts gold → Claude gera relatório .md para 3 diretores
3. **Envio automático** — envia relatórios para o Telegram via API HTTP direta (sem bot rodando), suportando cron

## Stack

- Python 3.10+, anthropic SDK (tool use), sqlalchemy + psycopg2-binary, pandas + tabulate, python-dotenv, python-telegram-bot v20+

## Comandos

```bash
# Setup
pip install -r requirements.txt
# Criar .env com: TELEGRAM, POSTGRES_URL, ANTHROPIC_API_KEY

# Modo interativo (bot Telegram com polling)
python bot.py

# Modo standalone (gera relatório + salva .md + envia Telegram se CHAT_ID configurado)
python agente.py
```

## Variáveis de Ambiente (`.env`)

| Variável | Descrição | Como obter |
|---|---|---|
| `TELEGRAM` | Token do bot | @BotFather no Telegram |
| `POSTGRES_URL` | `postgresql://user:pass@host:5432/dbname` | Supabase Dashboard |
| `ANTHROPIC_API_KEY` | Chave da API do Claude | console.anthropic.com |
| `CHAT_ID` | ID do chat para envio automático | Auto-registrado pelo `bot.py` na primeira interação |

## Arquitetura dos Arquivos

```
Supabase (PostgreSQL)
        │
        ▼
  db.py ── execute_query(sql): aceita apenas SELECT/WITH
        │
        ▼
agente.py
  ├── chat(pergunta)         → Claude + tool use SQL (max 10 iterações) → resposta
  ├── gerar_relatorio()      → 4 queries fixas → Claude → relatório .md
  └── enviar_telegram(texto) → API HTTP urllib (sem python-telegram-bot)
        │
        ▼
  bot.py (Telegram polling)
  ├── /start                 → boas-vindas + salva CHAT_ID no .env
  ├── /relatorio             → gera e envia relatório
  └── texto livre            → chat() responde
```

### Dois modos de operação

| Modo | Comando | Precisa do bot rodando? |
|---|---|---|
| **Interativo** | `python bot.py` | Sim |
| **Standalone** | `python agente.py` | Não |

## Tool Use (Chat Livre)

Ferramenta `executar_sql` exposta ao Claude:

```json
{
    "name": "executar_sql",
    "description": "Executa query SQL SELECT no banco PostgreSQL do e-commerce.",
    "input_schema": {
        "type": "object",
        "properties": {"sql": {"type": "string"}},
        "required": ["sql"]
    }
}
```

- Apenas SELECT/WITH são aceitos — `db.py` rejeita qualquer outra instrução
- Limite de 10 iterações por pergunta para evitar loop infinito
- System prompt inclui schema completo das 3 tabelas gold como contexto

## Relatório Executivo

**Queries fixas executadas:**
1. Resumo de vendas (últimos 7 dias) — `public_gold_sales.vendas_temporais`
2. Segmentação de clientes — `public_gold_cs.clientes_segmentacao`
3. Alertas de pricing por classificação — `public_gold_pricing.precos_competitividade`
4. Produtos críticos (`classificacao_preco = 'MAIS_CARO_QUE_TODOS'`, top 10 por diferença percentual)

Dados formatados via `DataFrame.to_markdown()` antes de enviar ao Claude. Relatório salvo como `relatorio_YYYY-MM-DD.md`.

**System prompt:** 3 seções (Comercial, Customer Success, Pricing), máx. 1 página por diretor, insights acionáveis com ações sugeridas, valores em R$.

## Envio Telegram

- `enviar_telegram()` usa `urllib` diretamente (não python-telegram-bot) — funciona sem bot rodando
- Mensagens > 4096 chars são splitadas automaticamente
- Fallback: se `parse_mode=Markdown` falhar, reenvia como texto puro
- `salvar_chat_id()` no `bot.py` atualiza `.env` na primeira interação do usuário

## Data Marts Gold (banco: Supabase PostgreSQL)

Schemas completos em `.llm/database.md`.

### `public_gold_sales.vendas_temporais` — granularidade: data_venda + hora_venda
`data_venda`, `ano_venda`, `mes_venda`, `dia_venda`, `dia_semana_nome` (em português), `hora_venda`, `receita_total`, `quantidade_total`, `total_vendas`, `total_clientes_unicos`, `ticket_medio`

### `public_gold_cs.clientes_segmentacao` — granularidade: 1 linha por cliente
`cliente_id`, `nome_cliente`, `estado`, `receita_total`, `total_compras`, `ticket_medio`, `primeira_compra`, `ultima_compra`, `segmento_cliente` (VIP/TOP_TIER/REGULAR), `ranking_receita`

Segmentação: VIP ≥ R$10.000 | TOP_TIER ≥ R$5.000 | REGULAR < R$5.000

### `public_gold_pricing.precos_competitividade` — granularidade: 1 linha por produto
`produto_id`, `nome_produto`, `categoria`, `marca`, `nosso_preco`, `preco_medio_concorrentes`, `preco_minimo_concorrentes`, `preco_maximo_concorrentes`, `total_concorrentes`, `diferenca_percentual_vs_media`, `diferenca_percentual_vs_minimo`, `classificacao_preco`, `receita_total`, `quantidade_total`

Classificações: `MAIS_CARO_QUE_TODOS` | `ACIMA_DA_MEDIA` | `NA_MEDIA` | `ABAIXO_DA_MEDIA` | `MAIS_BARATO_QUE_TODOS`  
Concorrentes: Mercado Livre, Amazon, Shopee, Magalu

## Regras

- Modelo Claude: `claude-sonnet-4-20250514`
- Logging com timestamp em cada etapa (início, queries, envio)
- `db.py` valida SQL antes de executar — rejeita tudo que não seja SELECT/WITH
- Agendamento via cron chama `python agente.py` diretamente
- `.env`, `__pycache__/`, `*.pyc` e `relatorio_*.md` não são commitados


# Agente de Relatorios Diarios

## Contexto
Script Python que consulta 3 Data Marts gold no PostgreSQL,
envia os dados para a API do Claude e gera um relatorio executivo
diario para 3 diretores (Comercial, CS, Pricing).

## Stack
- Python 3.10+
- anthropic (SDK)
- psycopg2-binary
- pandas
- python-dotenv

## Banco de Dados
Connection string via POSTGRES_URL no .env.
Ver .llm/database.md para schemas completos.

## API
Chave da Anthropic via ANTHROPIC_API_KEY no .env.
Usar modelo claude-sonnet-4-20250514 para custo baixo.

## Regras
- Nao commitar .env com credenciais
- Tratar erro de conexao antes de chamar a API
- Salvar relatorio como .md com data no nome
- Logging com timestamps em cada etapa