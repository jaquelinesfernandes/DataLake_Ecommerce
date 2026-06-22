# Agente de Dados — E-commerce Bot Telegram

Agente de inteligência de dados para e-commerce brasileiro que combina LLM (Claude) com dados em tempo real via PostgreSQL. Permite consultas analíticas em linguagem natural pelo Telegram e envio automático de relatórios executivos diários para diretores.

---

## Objetivo

Eliminar o gap entre os dados estruturados nos Data Marts gold e a tomada de decisão dos gestores — sem dashboards intermediários. O agente consulta o banco diretamente, interpreta os dados com IA e entrega insights acionáveis pelo Telegram, sob demanda ou de forma agendada.

**Três capacidades principais:**

| # | Capacidade | Como acionar |
|---|---|---|
| 1 | **Chat livre** — qualquer pergunta analítica respondida com SQL gerado pelo Claude | Mensagem de texto no Telegram |
| 2 | **Relatório executivo** — 4 queries fixas → Claude → relatório `.md` para 3 diretores | `/relatorio` no Telegram ou `python agente.py` |
| 3 | **Envio automático** — relatório enviado via API HTTP do Telegram sem bot rodando | Cron job chamando `python agente.py` |

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Supabase (PostgreSQL)                            │
│                                                                         │
│  public_gold_sales.vendas_temporais    ← métricas por dia/hora          │
│  public_gold_cs.clientes_segmentacao  ← segmentação VIP/TOP_TIER        │
│  public_gold_pricing.precos_competitividade ← comparativo concorrentes  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ SQLAlchemy + psycopg2
                               ▼
                   ┌───────────────────────┐
                   │        db.py          │
                   │  execute_query(sql)   │  ← aceita apenas SELECT/WITH
                   └───────────┬───────────┘
                               │
                               ▼
                   ┌───────────────────────────────────────┐
                   │             agente.py                 │
                   │                                       │
                   │  chat(pergunta)                       │
                   │    └─ Claude + tool use executar_sql  │
                   │         └─ até 10 iterações           │
                   │                                       │
                   │  gerar_relatorio()                    │
                   │    └─ 4 queries → Claude → .md        │
                   │                                       │
                   │  enviar_telegram(texto)               │
                   │    └─ urllib → API HTTP Telegram      │
                   └──────────┬────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
  ┌───────────────────────┐       ┌───────────────────────┐
  │        bot.py         │       │    Cron / Terminal    │
  │  (Telegram polling)   │       │   python agente.py    │
  │                       │       │                       │
  │  /start → boas-vindas │       │  Gera relatório       │
  │  /relatorio → rel.    │       │  Salva .md            │
  │  texto → chat()       │       │  Envia Telegram       │
  │  auto-salva CHAT_ID   │       │  (sem bot rodando)    │
  └───────────────────────┘       └───────────────────────┘
```

### Fluxo do Chat Livre (tool use)

```
Usuário → Telegram → bot.py → agente.chat()
                                    │
                                    ▼
                            Claude recebe pergunta
                            + schema do banco
                                    │
                                    ▼ (tool_use)
                            Claude gera SQL
                                    │
                                    ▼
                            db.execute_query(sql)
                            → PostgreSQL → DataFrame
                                    │
                                    ▼ (tool_result)
                            Claude analisa dados
                            + gera resposta em PT-BR
                                    │
                                    ▼
                    Telegram ← bot.py ← resposta formatada
```

### Arquitetura de Dados (Medalhão)

```
RAW        Bronze (views)     Silver (tables)       Gold (tables)
───────    ───────────────    ───────────────    ──────────────────────────
vendas  →  bronze_vendas   →  silver_vendas  ─┬→ vendas_temporais
clientes → bronze_clientes →  silver_clientes ┤→ clientes_segmentacao
produtos → bronze_produtos →  silver_produtos ┤
preco_*  → bronze_preco_*  →  silver_preco_*  ┘→ precos_competitividade
```

---

## Estrutura do Projeto

```
case-02-agente/
│
├── agente.py          # Lógica principal: chat(), gerar_relatorio(), enviar_telegram()
├── bot.py             # Bot Telegram com polling e auto-registro de CHAT_ID
├── db.py              # Conexão PostgreSQL via SQLAlchemy; valida SELECT/WITH
│
├── requirements.txt   # Dependências Python
├── .env               # Variáveis de ambiente (não commitado)
│
├── .llm/
│   ├── database.md    # Catálogo completo dos 3 Data Marts (schemas, regras, samples)
│   └── prd.md         # PRD técnico do projeto
│
└── relatorio_*.md     # Relatórios gerados (não commitados)
```

| Arquivo | Responsabilidade |
|---|---|
| `db.py` | Singleton de conexão SQLAlchemy. Rejeita qualquer SQL que não seja `SELECT` ou `WITH`. |
| `agente.py` | Três funções independentes: `chat()` usa tool use iterativo; `gerar_relatorio()` executa 4 queries fixas e chama Claude; `enviar_telegram()` usa `urllib` puro (sem bot). |
| `bot.py` | Interface Telegram com polling assíncrono. Handlers para `/start`, `/relatorio` e texto livre. Salva `CHAT_ID` automaticamente no `.env` na primeira interação. |

---

## Tecnologias

| Camada | Tecnologia | Versão | Papel |
|---|---|---|---|
| **LLM** | Anthropic Claude | `claude-sonnet-4-6` | Chat analítico com tool use + geração de relatório |
| **LLM SDK** | `anthropic` | ≥ 0.40.0 | Integração com API do Claude, tool use nativo |
| **Banco** | PostgreSQL | — | Armazenamento dos Data Marts gold |
| **Hospedagem DB** | Supabase | — | PostgreSQL gerenciado com connection pooler |
| **ORM / SQL** | SQLAlchemy | ≥ 2.0 | Engine de conexão e execução de queries |
| **Driver DB** | psycopg2-binary | ≥ 2.9.9 | Driver PostgreSQL para Python |
| **Dados** | pandas | ≥ 2.0 | Leitura de resultados SQL e formatação Markdown |
| **Tabelas MD** | tabulate | ≥ 0.9.0 | Dependência do `DataFrame.to_markdown()` |
| **Bot** | python-telegram-bot | ≥ 20.0 | Polling assíncrono, handlers de comandos |
| **HTTP Telegram** | urllib (stdlib) | — | Envio direto de mensagens sem bot rodando |
| **Config** | python-dotenv | ≥ 1.0.0 | Carregamento do `.env` |
| **Linguagem** | Python | 3.10+ | Runtime do projeto |

---

## Data Marts Gold

### `public_gold_sales.vendas_temporais`
Métricas de vendas agregadas por `data_venda + hora_venda`.
Colunas principais: `receita_total`, `total_vendas`, `total_clientes_unicos`, `ticket_medio`, `dia_semana_nome`.

### `public_gold_cs.clientes_segmentacao`
Um registro por cliente com segmentação por receita acumulada.

| Segmento | Critério |
|---|---|
| `VIP` | receita_total ≥ R$ 10.000 |
| `TOP_TIER` | receita_total ≥ R$ 5.000 |
| `REGULAR` | receita_total < R$ 5.000 |

### `public_gold_pricing.precos_competitividade`
Posicionamento de preço de cada produto vs Mercado Livre, Amazon, Shopee e Magalu.
Classificações: `MAIS_CARO_QUE_TODOS` · `ACIMA_DA_MEDIA` · `NA_MEDIA` · `ABAIXO_DA_MEDIA` · `MAIS_BARATO_QUE_TODOS`

> Schema completo com tipos, regras de negócio e sample data em `.llm/database.md`.

---

## Configuração

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie o arquivo `.env` na raiz do projeto:

```env
POSTGRES_URL=postgresql://user:pass@host:5432/dbname
TELEGRAM=token-do-bot
ANTHROPIC_API_KEY=sk-ant-...
CHAT_ID=                     # preenchido automaticamente pelo bot.py
```

| Variável | Como obter |
|---|---|
| `POSTGRES_URL` | Supabase Dashboard → Settings → Database → Connection String |
| `TELEGRAM` | @BotFather no Telegram → `/newbot` |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `CHAT_ID` | Automático — salvo na primeira interação com `/start` |

> **Atenção:** Senhas com caracteres especiais (`[`, `]`, `$`, `@`) na connection string devem ser URL-encoded. Ex: `$` → `%24`, `[` → `%5B`, `]` → `%5D`.

### 3. Registrar CHAT_ID (uma vez)

```bash
python bot.py
```

No Telegram, envie `/start` para o bot. O `CHAT_ID` é salvo automaticamente no `.env`.

---

## Como Executar

### Modo interativo — bot Telegram

```bash
python bot.py
```

Mantém o bot rodando com polling. Suporta chat livre e `/relatorio` sob demanda.

### Modo standalone — relatório + envio automático

```bash
python agente.py
```

Não requer bot rodando. Executa as 4 queries, gera o relatório com Claude, salva `relatorio_YYYY-MM-DD.md` e envia para o Telegram se `CHAT_ID` estiver configurado.

### Agendamento via cron

```bash
# Relatório diário às 8h
0 8 * * * cd /caminho/projeto && python agente.py >> /tmp/agente.log 2>&1
```

---

## Dois Modos de Operação

| Modo | Comando | Bot rodando? | Caso de uso |
|---|---|---|---|
| **Interativo** | `python bot.py` | Sim | Chat analítico + relatório sob demanda |
| **Standalone** | `python agente.py` | Não | Relatório agendado via cron |

---

## Segurança

- `db.py` valida o SQL antes de executar — rejeita tudo que não seja `SELECT` ou `WITH`, impedindo escrita ou DDL acidental.
- `.env` não é commitado (`.gitignore`).
- Relatórios gerados (`relatorio_*.md`) não são commitados.
- Tool use do Claude limitado a 10 iterações por pergunta para evitar loops infinitos.
