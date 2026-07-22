# 🛒 DataLake E-commerce — Pipeline Analítico com dbt, Dashboard e Agente de IA

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-1.x-FF694B?style=flat&logo=dbt&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

Projeto completo de **engenharia de dados e inteligência analítica** para um e-commerce brasileiro. Implementa uma **Arquitetura Medalhão** (Bronze → Silver → Gold) sobre PostgreSQL no Supabase, com dois cases de consumo dos dados: um **dashboard executivo** em Streamlit e um **agente de IA** com bot no Telegram.

---

## 🗺️ Visão Geral do Projeto

```
  Supabase Storage (S3)
         │
         │  datalake_el.py  (Extract & Load)
         ▼
  PostgreSQL — schema public (raw)
         │
         │  dbt run  (Transform)
         ▼
  ┌─────────────┐
  │   BRONZE    │  views — cópia fiel da fonte
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │   SILVER    │  tables — limpeza, tipagem e colunas calculadas
  └──────┬──────┘
         │
         ▼
  ┌─────────────────────────────────┐
  │              GOLD               │  tables — KPIs prontos para consumo
  │  sales  │  customer_success  │  pricing  │
  └────┬────────────────────────────┘
       │
       ├──► 📊 Case 01 — Dashboard Streamlit (3 páginas)
       │
       └──► 🤖 Case 02 — Agente IA + Bot Telegram (chat livre + relatório diário)
```

---

## 🏗️ Fases do Desenvolvimento

### 🔵 Fase 1 — Ingestão de Dados (`datalake_el.py`)

Script de **Extract & Load** que conecta ao Supabase Storage (S3-compatible), baixa os arquivos `.parquet` das 4 tabelas brutas e os carrega no PostgreSQL, criando as tabelas raw que servem de fonte para o pipeline dbt.

```
Supabase Storage  →  datalake_el.py  →  PostgreSQL (schema public)
  produtos.parquet                         raw.produtos
  clientes.parquet                         raw.clientes
  vendas.parquet                           raw.vendas
  preco_competidores.parquet               raw.preco_competidores
```

---

### 🔵 Fase 2 — Modelagem de Dados com dbt

Construção do pipeline de transformação completo seguindo a **Arquitetura Medalhão**:

| Camada | Materialização | Schema | Modelos | Objetivo |
|--------|---------------|--------|---------|----------|
| Bronze | `view` | `bronze` | 4 | Cópia exata das tabelas brutas, sem transformação |
| Silver | `table` | `silver` | 4 | Limpeza, tipagem correta e colunas calculadas |
| Intermediate | `ephemeral` | — | 2 | CTEs reutilizáveis, sem tabela física no banco |
| Gold | `table` | `gold_sales`, `gold_cs`, `gold_pricing` | 3 | KPIs agregados com regras de negócio |

**Destaques:**
- Silver incremental em `silver_vendas` (só processa registros novos)
- Macros reutilizáveis para segmentação (`get_segmento_cliente`) e faixa de preço (`get_faixa_preco`)
- Testes de qualidade de dados: `not_null`, `unique`, `accepted_values`, `relationships`
- Variáveis de negócio configuráveis (`segmentacao_vip_threshold`, `segmentacao_top_tier_threshold`)
- Freshness checks nas sources e exposures documentadas

---

### 📊 Fase 3 — Dashboard Executivo (Case 01)

Dashboard interativo em Streamlit para 3 diretores, consumindo os Data Marts gold em tempo real.

**Páginas:**
- **Vendas** — receita diária, volume por hora, receita por dia da semana, filtro por mês
- **Clientes** — distribuição por segmento (VIP/TOP_TIER/REGULAR), top 10 por receita, mapa por estado
- **Pricing** — posicionamento vs concorrência, scatter competitividade × volume, alertas de preço

---

### 🤖 Fase 4 — Agente de IA com Bot Telegram (Case 02)

Sistema de inteligência analítica com 3 capacidades:

1. **Chat livre** — Claude consulta o banco via tool use (SQL dinâmico) e responde qualquer pergunta analítica em português
2. **Relatório executivo** — 4 queries fixas nos Data Marts gold → Claude gera relatório `.md` para 3 diretores
3. **Envio automático** — envia relatórios diretamente para o Telegram via API HTTP (sem bot rodando), compatível com cron

---

## 🛠️ Stack Tecnológica

### Pipeline de Dados
| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| **dbt Core** | 1.x | Orquestração e transformação de dados |
| **PostgreSQL** | 15 | Banco de dados analítico |
| **Supabase** | — | Host gerenciado do PostgreSQL + Storage S3-compatible |
| **boto3** | — | Leitura dos arquivos `.parquet` do Supabase Storage |
| **dbt-utils** | — | Macros utilitárias |
| **dbt-expectations** | — | Testes de qualidade avançados |
| **dbt-date** | — | Manipulação de datas |

### Dashboard (Case 01)
| Tecnologia | Uso |
|-----------|-----|
| **Python 3.10+** | Linguagem principal |
| **Streamlit** | Framework de dashboard |
| **Plotly** | Gráficos interativos |
| **SQLAlchemy + psycopg2** | Conexão com PostgreSQL |
| **pandas** | Manipulação de dados |
| **python-dotenv** | Variáveis de ambiente |

### Agente de IA (Case 02)
| Tecnologia | Uso |
|-----------|-----|
| **Python 3.10+** | Linguagem principal |
| **Anthropic SDK** | Claude com tool use (SQL dinâmico) |
| **python-telegram-bot v20+** | Bot Telegram assíncrono |
| **SQLAlchemy + psycopg2** | Conexão com PostgreSQL |
| **pandas + tabulate** | Formatação de dados para o LLM |
| **python-dotenv** | Variáveis de ambiente |

---

## 📁 Estrutura do Projeto

```
DataLake_Ecommerce/
├── datalake_el.py                        # Script EL: Supabase Storage → PostgreSQL
├── requirements.txt                      # Dependências do script EL
├── .env.example                          # Template de variáveis de ambiente (copiar para .env)
├── .gitignore
└── dbt_ecommerce/
    ├── dbt_project.yml                   # Configuração principal
    ├── packages.yml                      # Pacotes dbt
    ├── models/
    │   ├── _sources.yml                  # Declaração das tabelas brutas (raw)
    │   ├── exposures.yml                 # Dashboard e agente como exposures
    │   ├── bronze/
    │   │   ├── schema.yml
    │   │   ├── bronze_vendas.sql
    │   │   ├── bronze_clientes.sql
    │   │   ├── bronze_produtos.sql
    │   │   └── bronze_preco_competidores.sql
    │   ├── silver/
    │   │   ├── schema.yml
    │   │   ├── silver_vendas.sql         # Incremental
    │   │   ├── silver_clientes.sql
    │   │   ├── silver_produtos.sql
    │   │   └── silver_preco_competidores.sql
    │   ├── intermediate/
    │   │   ├── int_receita_por_cliente.sql   # Ephemeral
    │   │   └── int_vendas_por_produto.sql    # Ephemeral
    │   └── gold/
    │       ├── sales/
    │       │   ├── schema.yml
    │       │   └── vendas_temporais.sql
    │       ├── customer_success/
    │       │   ├── schema.yml
    │       │   └── clientes_segmentacao.sql
    │       └── pricing/
    │           ├── schema.yml
    │           └── precos_competitividade.sql
    ├── macros/
    │   ├── get_segmento_cliente.sql
    │   └── get_faixa_preco.sql
    ├── snapshots/
    │   └── snapshot_preco_competidores.sql
    ├── case-01-dashboard/                # Dashboard Streamlit
    │   ├── app.py
    │   ├── requirements.txt
    │   └── .llm/
    │       ├── prd-dashboard.md
    │       └── database.md
    └── case-02-agente/                   # Agente IA + Bot Telegram
        ├── db.py
        ├── agente.py
        ├── bot.py
        ├── requirements.txt
        └── .llm/
            ├── prd.md
            └── database.md
```

---

## 🗃️ Fontes de Dados

Quatro tabelas no schema `public` do PostgreSQL:

| Tabela | Registros | Descrição |
|--------|-----------|-----------|
| `raw.vendas` | ~3.020 | Transações de venda (id_venda, data_venda, id_cliente, id_produto, quantidade, preco_unitario, canal_venda) |
| `raw.clientes` | 50 | Cadastro de clientes (id_cliente, nome_cliente, estado, pais, data_cadastro) |
| `raw.produtos` | 215 | Catálogo de produtos (id_produto, nome_produto, categoria, marca, preco_atual) |
| `raw.preco_competidores` | ~728 | Preços de concorrentes — Mercado Livre, Amazon, Shopee, Magalu |

---

## 📦 Data Marts Gold

### 📈 `gold_sales.vendas_temporais`
Métricas de venda agregadas por data e hora. Responde: *como evoluiu o faturamento ao longo do tempo?*

| Coluna | Descrição |
|--------|-----------|
| `data_venda`, `ano_venda`, `mes_venda`, `dia_venda` | Dimensões de data |
| `dia_semana_nome` | Nome do dia em português (Segunda … Domingo) |
| `hora_venda` | Hora do dia (0–23) |
| `receita_total` | Soma da receita no período |
| `quantidade_total` | Itens vendidos |
| `total_vendas` | Pedidos distintos |
| `total_clientes_unicos` | Clientes distintos |
| `ticket_medio` | Receita média por transação |

### 👥 `gold_cs.clientes_segmentacao`
Segmentação de clientes por receita acumulada. Responde: *quem são meus melhores clientes?*

| Coluna | Descrição |
|--------|-----------|
| `cliente_id`, `nome_cliente`, `estado` | Identificação |
| `receita_total`, `total_compras`, `ticket_medio` | Métricas de valor |
| `primeira_compra`, `ultima_compra` | Ciclo de vida |
| `segmento_cliente` | `VIP` / `TOP_TIER` / `REGULAR` (configurável) |
| `ranking_receita` | Posição por receita decrescente |

**Thresholds de segmentação** (configuráveis via `dbt_project.yml`):

| Segmento | Critério |
|----------|----------|
| `VIP` | receita ≥ R$ 10.000 |
| `TOP_TIER` | receita ≥ R$ 5.000 |
| `REGULAR` | receita < R$ 5.000 |

### 💰 `gold_pricing.precos_competitividade`
Comparativo de preços vs concorrência. Responde: *como estamos posicionados no mercado?*

| Coluna | Descrição |
|--------|-----------|
| `produto_id`, `nome_produto`, `categoria`, `marca` | Identificação |
| `nosso_preco` | Preço atual praticado |
| `preco_medio_concorrentes`, `preco_minimo_concorrentes`, `preco_maximo_concorrentes` | Benchmark de mercado |
| `total_concorrentes` | Concorrentes com dado disponível |
| `diferenca_percentual_vs_media`, `diferenca_percentual_vs_minimo` | Posicionamento relativo |
| `classificacao_preco` | `MAIS_CARO_QUE_TODOS` / `ACIMA_DA_MEDIA` / `NA_MEDIA` / `ABAIXO_DA_MEDIA` / `MAIS_BARATO_QUE_TODOS` |
| `receita_total`, `quantidade_total` | Impacto em vendas |

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.10+
- Conta no [Supabase](https://supabase.com) com projeto PostgreSQL e Storage configurados
- Token de bot Telegram (via `@BotFather`) e chave da API Anthropic — apenas para o Case 02

---

### Passo 1 — Ingestão de dados (`datalake_el.py`)

```bash
# Na raiz do projeto
pip install -r requirements.txt

# Copiar o template e preencher as credenciais
cp .env.example .env
```

Edite o `.env` com os valores do seu projeto Supabase:

```env
S3_ENDPOINT_URL=https://SEU_PROJECT_REF.storage.supabase.co/storage/v1/s3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
BUCKET_NAME=datalake_ecommerce
DATABASE_URL=postgresql+psycopg2://postgres:SUA_SENHA@db.SEU_PROJECT_REF.supabase.co:6543/postgres
```

> As chaves S3 estão em **Supabase Dashboard → Storage → S3 Connection**.  
> O `PROJECT_REF` é o ID do projeto (ex: `abcdefghijklmnop`).

```bash
python datalake_el.py
```

---

### Passo 2 — Pipeline dbt

```bash
cd dbt_ecommerce
pip install dbt-postgres
```

Configure o `profiles.yml` em `~/.dbt/profiles.yml`:

```yaml
dbt_ecommerce:
  outputs:
    dev:
      type: postgres
      host: db.SEU_PROJECT_REF.supabase.co
      port: 5432
      dbname: postgres
      user: postgres
      pass: SUA_SENHA
      schema: public
      threads: 1
  target: dev
```

```bash
dbt debug                              # Verificar conexão
dbt deps                               # Instalar pacotes
dbt run                                # Executar todos os modelos
dbt test                               # Rodar testes de qualidade
dbt docs generate && dbt docs serve    # Gerar documentação
```

```bash
# Executar por camada
dbt run --select tag:bronze
dbt run --select tag:silver
dbt run --select tag:gold

# Executar modelo com toda a cadeia upstream
dbt run --select +vendas_temporais

# Sobrescrever thresholds de segmentação
dbt run --vars '{"segmentacao_vip_threshold": 15000}'
```

---

### Passo 3a — Dashboard Streamlit (Case 01)

```bash
cd dbt_ecommerce/case-01-dashboard
pip install -r requirements.txt

# Criar .env com credenciais Supabase:
# SUPABASE_HOST=db.SEU_PROJECT_REF.supabase.co
# SUPABASE_USER=postgres
# SUPABASE_PASSWORD=SUA_SENHA
# SUPABASE_DB=postgres
# SUPABASE_PORT=5432

streamlit run app.py
# Acessa em http://localhost:8501
```

---

### Passo 3b — Agente IA + Bot Telegram (Case 02)

```bash
cd dbt_ecommerce/case-02-agente
pip install -r requirements.txt

# Criar .env:
# TELEGRAM=token-do-botfather
# POSTGRES_URL=postgresql://postgres:SUA_SENHA@db.SEU_PROJECT_REF.supabase.co:5432/postgres
# ANTHROPIC_API_KEY=sk-ant-...
# CHAT_ID=  (preenchido automaticamente na primeira interação)

# Modo interativo (bot com polling)
python bot.py

# Modo standalone (gera relatório + envia Telegram se CHAT_ID configurado)
python agente.py
```

**Comandos do bot:**

| Comando | Ação |
|---------|------|
| `/start` | Boas-vindas + registra CHAT_ID automaticamente |
| `/relatorio` | Gera e envia relatório executivo completo |
| Texto livre | Chat analítico — Claude consulta o banco e responde |

---

## 🔗 Linhagem de Dados

```
raw.vendas             → bronze_vendas             → silver_vendas             ┐
raw.clientes           → bronze_clientes           → silver_clientes           ├─► clientes_segmentacao
                                                                                │
raw.vendas             → bronze_vendas             → silver_vendas             ┘
                                                                                ┐
raw.produtos           → bronze_produtos           → silver_produtos           ├─► precos_competitividade
raw.preco_competidores → bronze_preco_competidores → silver_preco_competidores ┘

raw.vendas             → bronze_vendas             → silver_vendas              ──► vendas_temporais
```

---

## 🎓 Conceitos de Aprendizado

### 🏛️ Engenharia de Dados

| Conceito | Onde foi aplicado |
|----------|------------------|
| **Arquitetura Medalhão (Bronze → Silver → Gold)** | Organização das camadas do pipeline dbt — separação clara entre ingestão, limpeza e consumo |
| **ELT (Extract, Load, Transform)** | Dados carregados primeiro no banco (Supabase) e transformados pelo dbt, ao contrário do ETL tradicional |
| **Modelo Incremental** | `silver_vendas` processa apenas registros novos a cada execução, evitando reprocessamento completo |
| **Modelo Ephemeral** | `int_receita_por_cliente` e `int_vendas_por_produto` existem apenas como CTEs em tempo de execução, sem custo de storage |
| **Data Mart** | Cada tabela gold é um Data Mart especializado por domínio (Sales, Customer Success, Pricing), pronto para consumo direto |
| **Data Lineage** | Rastreabilidade completa de cada coluna desde a fonte raw até o KPI final, visualizável via `dbt docs` |
| **Data Quality** | Testes genéricos (`not_null`, `unique`, `relationships`, `accepted_values`) e freshness checks nas sources |
| **Schema separation** | Cada camada em seu próprio schema PostgreSQL (`bronze`, `silver`, `gold_sales`, `gold_cs`, `gold_pricing`) |

---

### 🔧 dbt (Data Build Tool)

| Conceito | Como foi usado |
|----------|---------------|
| **Sources** | Declaração das tabelas brutas em `_sources.yml` com freshness checks e testes de coluna |
| **Refs** | `{{ ref('model') }}` para rastrear dependências entre modelos e construir o DAG automaticamente |
| **Macros** | `get_segmento_cliente()` e `get_faixa_preco()` encapsulam regras de negócio reutilizáveis em Jinja |
| **Vars** | `segmentacao_vip_threshold` e `segmentacao_top_tier_threshold` tornam os thresholds configuráveis via CLI |
| **Tags** | `bronze`, `silver`, `gold`, `kpi` permitem executar subconjuntos de modelos com `--select tag:X` |
| **Config blocks** | `{{ config(materialized='incremental', unique_key='id_venda') }}` define o comportamento de cada modelo |
| **Exposures** | Dashboard e agente declarados como consumers do pipeline, documentando quem depende de cada modelo |
| **Packages** | `dbt-utils`, `dbt-expectations` e `dbt-date` adicionados via `packages.yml` para estender as capacidades |

---

### 🤖 Inteligência Artificial e LLMs

| Conceito | Como foi aplicado |
|----------|-----------------|
| **Tool Use (Function Calling)** | Claude recebe a ferramenta `executar_sql` e decide autonomamente quando e quais queries SQL executar para responder uma pergunta |
| **Agentic Loop** | Loop de até 10 iterações: Claude chama ferramenta → recebe resultado → decide se precisa de mais dados → gera resposta final |
| **System Prompt como contexto** | Schema completo das 3 tabelas gold injetado no system prompt, orientando o Claude a gerar SQL correto sem alucinações de coluna |
| **LLM como analista (Text-to-SQL)** | Em vez de SQL fixo, o usuário faz perguntas em português e o Claude traduz para queries SQL dinamicamente |
| **Prompt Engineering** | System prompts distintos para chat livre (conciso, analítico) e relatório executivo (estruturado, com persona de diretor) |
| **Fallback de conteúdo** | Se a API do Claude falhar, o agente salva os dados brutos formatados em Markdown como relatório de emergência |

---

### 📊 Visualização de Dados

| Conceito | Onde aparece |
|----------|-------------|
| **KPI Cards** | Métricas-chave em destaque no topo de cada página do dashboard com HTML/CSS customizado |
| **Série temporal** | Gráfico de linha com área preenchida para receita diária — comunica tendência e volume simultaneamente |
| **Gráfico de barras** | Comparações categóricas (dia da semana, hora, segmento, estado, categoria de produto) |
| **Gráfico de pizza / donut** | Distribuição proporcional de segmentos de cliente e classificações de preço |
| **Scatter plot com bolhas** | Competitividade de preço vs volume de vendas — tamanho da bolha = receita, cor = classificação |
| **Caching de queries** | `@st.cache_data(ttl=600)` evita recarregar dados do banco a cada interação do usuário |
| **Layout responsivo** | `st.columns()` para organizar métricas e gráficos lado a lado com `layout="wide"` |

---

### 🔒 Boas Práticas de Engenharia de Software

| Prática | Implementação |
|---------|--------------|
| **Separação de responsabilidades** | `db.py` (conexão), `agente.py` (lógica de IA), `bot.py` (interface Telegram) — cada arquivo com uma única função |
| **Variáveis de ambiente** | Credenciais em `.env` via `python-dotenv`, nunca hardcoded no código — template disponível em `.env.example` |
| **Validação de entrada (SQL)** | `db.py` rejeita qualquer SQL que não comece com `SELECT` ou `WITH` e bloqueia palavras-chave DML (`DELETE`, `UPDATE`, `INSERT`, `DROP`, etc.) via regex — prevenindo operações destrutivas mesmo dentro de CTEs |
| **Gestão de erros** | Tratamento separado para falha de banco (antes de chamar a API) e falha de API (fallback com dados brutos); erros internos logados no servidor sem expor detalhes ao usuário |
| **Auto-registro** | `salvar_chat_id()` atualiza o `.env` na primeira interação, sem precisar de configuração manual |
| **Paginação de mensagens** | Split automático em chunks de 4.096 chars com fallback de Markdown para texto puro no Telegram |
| **Limites de segurança** | Máximo de 10 iterações no agentic loop para prevenir loops infinitos e custos inesperados de API |
