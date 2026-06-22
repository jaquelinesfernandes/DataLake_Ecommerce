# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dashboard E-commerce

Dashboard Streamlit para 3 diretores de um e-commerce. Conecta no banco PostgreSQL (Supabase) e consome 3 Data Marts gold.

## Stack

- Python 3.10+, Streamlit, Plotly, psycopg2-binary, pandas, python-dotenv

## Comandos

```bash
# Setup
cp .env.example .env
# Editar .env com credenciais reais do Supabase
pip install -r requirements.txt

# Rodar o dashboard
streamlit run app.py
# Abre em http://localhost:8501
```

## Banco de Dados

Conexão via variáveis de ambiente no `.env`:

```
SUPABASE_HOST=seu-host.supabase.co
SUPABASE_PORT=5432
SUPABASE_DB=postgres
SUPABASE_USER=seu-usuario
SUPABASE_PASSWORD=sua-senha
```

Schemas completos em `.llm/database.md`.

## Arquitetura do App

```
Supabase (PostgreSQL)
    ├── public_gold_sales.vendas_temporais      → Página: Vendas
    ├── public_gold_cs.clientes_segmentacao     → Página: Clientes
    └── public_gold_pricing.precos_competitividade → Página: Pricing
            │
            ▼
    app.py (Streamlit, layout=wide)
    └── Sidebar: navegação entre as 3 páginas
```

### Estrutura do app.py

- `app.py` — arquivo único com as 3 páginas
- Sidebar com `st.sidebar.selectbox` ou `st.sidebar.radio` para navegar entre Vendas / Clientes / Pricing
- Função de conexão reutilizável que lê `.env` e retorna `pandas.DataFrame` a partir de SQL
- Sem cache agressivo: dados mudam após cada `dbt run`

### Páginas e tabelas fonte

| Página | Diretor | Tabela Gold |
|--------|---------|-------------|
| Vendas | Comercial | `public_gold_sales.vendas_temporais` |
| Clientes | Customer Success | `public_gold_cs.clientes_segmentacao` |
| Pricing | Pricing | `public_gold_pricing.precos_competitividade` |

Cada página exibe 4 KPIs com `st.columns(4)` + `st.metric`, gráficos Plotly e tabelas/alertas. Ver `.llm/prd-dashboard.md` para especificação completa de cada página.

## Data Marts Gold (resumo)

### `vendas_temporais` — granularidade: data_venda + hora_venda
Colunas principais: `data_venda`, `ano_venda`, `mes_venda`, `dia_semana_nome`, `hora_venda`, `receita_total`, `quantidade_total`, `total_vendas`, `total_clientes_unicos`, `ticket_medio`

### `clientes_segmentacao` — granularidade: 1 linha por cliente
Colunas principais: `cliente_id`, `nome_cliente`, `estado`, `receita_total`, `total_compras`, `ticket_medio`, `primeira_compra`, `ultima_compra`, `segmento_cliente` (VIP/TOP_TIER/REGULAR), `ranking_receita`

Segmentação: VIP ≥ R$10.000 | TOP_TIER ≥ R$5.000 | REGULAR < R$5.000

### `precos_competitividade` — granularidade: 1 linha por produto
Colunas principais: `produto_id`, `nome_produto`, `categoria`, `marca`, `nosso_preco`, `preco_medio_concorrentes`, `preco_minimo_concorrentes`, `preco_maximo_concorrentes`, `diferenca_percentual_vs_media`, `classificacao_preco`, `receita_total`, `quantidade_total`

Classificações: `MAIS_CARO_QUE_TODOS` | `ACIMA_DA_MEDIA` | `NA_MEDIA` | `ABAIXO_DA_MEDIA` | `MAIS_BARATO_QUE_TODOS`

Concorrentes monitorados: Mercado Livre, Amazon, Shopee, Magalu

## Regras

- Não commitar `.env` com credenciais
- Formatar valores monetários em reais (R$) com ponto de milhar e vírgula decimal
- Usar Plotly para todos os gráficos (não matplotlib)
- Layout wide: `st.set_page_config(layout="wide")`
- Tratar erros de conexão com mensagem amigável ao usuário
