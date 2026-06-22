import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv(interpolate=False)

st.set_page_config(page_title="E-commerce Analytics", layout="wide")

# ─── Design tokens ────────────────────────────────────────────────────────────

NAVY    = "#0F172A"
SLATE   = "#1E293B"
INDIGO  = "#6366F1"
EMERALD = "#10B981"
AMBER   = "#F59E0B"
MUTED   = "#64748B"
BORDER  = "#E2E8F0"
ICE     = "#F8FAFC"

MESES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}
DIAS_SEMANA_ORDER = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
PRECO_COLORS = {
    "MAIS_BARATO_QUE_TODOS": "#2ecc71",
    "ABAIXO_DA_MEDIA":       "#82e0aa",
    "NA_MEDIA":              "#f7dc6f",
    "ACIMA_DA_MEDIA":        "#e59866",
    "MAIS_CARO_QUE_TODOS":   "#e74c3c",
}

# ─── CSS ──────────────────────────────────────────────────────────────────────

def inject_css() -> None:
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}

/* ── Sidebar ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {{
    background: {NAVY} !important;
}}
[data-testid="stSidebar"] *:not(svg):not(path) {{
    color: #CBD5E1 !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: {SLATE} !important;
    margin: 0.75rem 0 !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {{
    gap: 4px !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
    border-radius: 8px !important;
    padding: 9px 14px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: background 0.15s !important;
    cursor: pointer !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
    background: rgba(99,102,241,0.18) !important;
    color: #FFFFFF !important;
}}

/* ── Layout ── */
.stApp {{
    background: {ICE} !important;
}}
.main .block-container {{
    padding: 1.75rem 2rem 2rem !important;
    max-width: 100% !important;
}}

/* ── Chart cards ── */
[data-testid="stPlotlyChart"] {{
    background: #FFFFFF !important;
    border-radius: 12px !important;
    border: 1px solid {BORDER} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.04) !important;
    padding: 4px !important;
}}

/* ── Dataframe card ── */
[data-testid="stDataFrame"] {{
    border-radius: 12px !important;
    border: 1px solid {BORDER} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    overflow: hidden !important;
}}

/* ── Form control labels ── */
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {{
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    color: {MUTED} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}}
</style>
""", unsafe_allow_html=True)


# ─── UI helpers ───────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str, accent: str) -> None:
    st.markdown(f"""
<div style="margin-bottom:1.5rem;padding-bottom:1.25rem;border-bottom:1px solid {BORDER};">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:2px;">
    <div style="width:4px;height:28px;background:{accent};border-radius:2px;flex-shrink:0;"></div>
    <h1 style="margin:0;font-size:1.65rem;font-weight:800;color:{NAVY};letter-spacing:-0.03em;">{title}</h1>
  </div>
  <p style="margin:0 0 0 14px;font-size:0.82rem;color:{MUTED};font-weight:400;">{subtitle}</p>
</div>
""", unsafe_allow_html=True)


def kpi_card(label: str, value: str, accent: str) -> str:
    return f"""
<div style="background:#FFFFFF;border-radius:12px;padding:18px 20px 16px;
            box-shadow:0 1px 4px rgba(0,0,0,0.06),0 6px 20px rgba(0,0,0,0.05);
            border:1px solid {BORDER};border-top:3px solid {accent};
            height:100%;box-sizing:border-box;">
  <p style="margin:0;font-size:0.68rem;font-weight:700;color:{MUTED};
            text-transform:uppercase;letter-spacing:0.1em;">{label}</p>
  <p style="margin:10px 0 0;font-size:1.85rem;font-weight:800;color:{NAVY};
            letter-spacing:-0.03em;line-height:1.1;">{value}</p>
</div>"""


def section_label(text: str) -> None:
    st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin:1.75rem 0 0.75rem;">
  <span style="font-size:0.7rem;font-weight:700;color:{MUTED};
               text-transform:uppercase;letter-spacing:0.1em;white-space:nowrap;">{text}</span>
  <div style="flex:1;height:1px;background:{BORDER};"></div>
</div>
""", unsafe_allow_html=True)


def chart_theme(fig, accent: str = INDIGO):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor=ICE,
        font=dict(family="Inter, sans-serif", color="#334155", size=11),
        title=dict(
            font=dict(size=13, color=NAVY),
            x=0, xanchor="left",
            pad=dict(b=12),
        ),
        margin=dict(t=48, b=32, l=44, r=20),
        xaxis=dict(
            gridcolor=BORDER, linecolor="#CBD5E1",
            tickfont=dict(size=10, color=MUTED),
            zerolinecolor=BORDER,
        ),
        yaxis=dict(
            gridcolor=BORDER, linecolor="#CBD5E1",
            tickfont=dict(size=10, color=MUTED),
            zerolinecolor=BORDER,
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=BORDER, borderwidth=1,
            font=dict(size=10),
        ),
        hoverlabel=dict(
            bgcolor=NAVY,
            font=dict(color="white", size=11, family="Inter"),
            bordercolor=NAVY,
        ),
    )
    return fig


# ─── Banco de dados ───────────────────────────────────────────────────────────

def _get_engine():
    host = os.getenv("SUPABASE_HOST")
    if host:
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=os.getenv("SUPABASE_USER"),
            password=os.getenv("SUPABASE_PASSWORD"),
            host=host,
            port=int(os.getenv("SUPABASE_PORT", "5432")),
            database=os.getenv("SUPABASE_DB", "postgres"),
        )
        return create_engine(url, connect_args={"sslmode": "require"})
    raw = os.getenv("POSTGRES_URL", "")
    if raw:
        if raw.startswith("postgresql://"):
            raw = raw.replace("postgresql://", "postgresql+psycopg2://", 1)
        return create_engine(raw, connect_args={"sslmode": "require"})
    raise ValueError("Nenhuma variável de conexão encontrada no .env")


@st.cache_data(ttl=600)
def query_df(sql: str) -> pd.DataFrame:
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as exc:
        st.error(f"Erro ao conectar ao banco de dados: {exc}")
        st.stop()


# ─── Formatadores ─────────────────────────────────────────────────────────────

def brl(v: float) -> str:
    return f"R$ {v:_.2f}".replace(".", ",").replace("_", ".")

def intbr(v) -> str:
    return f"{int(v):,}".replace(",", ".")

def pct(v: float) -> str:
    return f"{'+' if v > 0 else ''}{v:.1f}%"


# ─── Página: Vendas ───────────────────────────────────────────────────────────

def page_vendas():
    page_header("Vendas", "Performance comercial e análise temporal de receita", INDIGO)

    df = query_df("SELECT * FROM public_gold_sales.vendas_temporais")

    meses = sorted(int(m) for m in df["mes_venda"].unique())
    sel_mes = st.selectbox(
        "Filtrar por mês",
        options=[0] + meses,
        format_func=lambda m: "Todos os meses" if m == 0 else MESES_PT.get(m, str(m)),
    )
    if sel_mes != 0:
        df = df[df["mes_venda"] == sel_mes]

    receita  = df["receita_total"].sum()
    vendas   = df["total_vendas"].sum()
    ticket   = receita / vendas if vendas else 0
    clientes = df.groupby("data_venda")["total_clientes_unicos"].max().sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Receita Total",   brl(receita),    INDIGO),    unsafe_allow_html=True)
    c2.markdown(kpi_card("Total de Vendas", intbr(vendas),   "#8B5CF6"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Ticket Médio",    brl(ticket),     "#06B6D4"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Clientes Únicos", intbr(clientes), EMERALD),   unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    # Receita por dia — linha com área preenchida
    df_dia = (df.groupby("data_venda", as_index=False)["receita_total"]
                .sum().sort_values("data_venda"))
    fig1 = px.line(df_dia, x="data_venda", y="receita_total", title="Receita Diária",
                   labels={"data_venda": "Data", "receita_total": "Receita (R$)"})
    fig1.update_traces(
        line=dict(color=INDIGO, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.08)",
    )
    st.plotly_chart(chart_theme(fig1), width="stretch")

    col1, col2 = st.columns(2)

    # Receita por dia da semana
    df_sem = df.groupby("dia_semana_nome", as_index=False)["receita_total"].sum()
    df_sem["dia_semana_nome"] = pd.Categorical(
        df_sem["dia_semana_nome"], categories=DIAS_SEMANA_ORDER, ordered=True
    )
    df_sem = df_sem.sort_values("dia_semana_nome")
    fig2 = px.bar(df_sem, x="dia_semana_nome", y="receita_total",
                  title="Receita por Dia da Semana",
                  labels={"dia_semana_nome": "Dia", "receita_total": "Receita (R$)"})
    fig2.update_traces(marker_color=INDIGO, marker_line_width=0)
    col1.plotly_chart(chart_theme(fig2), width="stretch")

    # Volume por hora
    df_hora = (df.groupby("hora_venda", as_index=False)["total_vendas"]
                 .sum().sort_values("hora_venda"))
    fig3 = px.bar(df_hora, x="hora_venda", y="total_vendas",
                  title="Volume de Vendas por Hora",
                  labels={"hora_venda": "Hora", "total_vendas": "Nº de Vendas"})
    fig3.update_traces(marker_color="#8B5CF6", marker_line_width=0)
    col2.plotly_chart(chart_theme(fig3), width="stretch")


# ─── Página: Clientes ─────────────────────────────────────────────────────────

SEG_COLORS = {"VIP": INDIGO, "TOP_TIER": "#8B5CF6", "REGULAR": "#C4B5FD"}


def page_clientes():
    page_header("Clientes", "Segmentação e análise de valor da base de clientes", EMERALD)

    df = query_df("SELECT * FROM public_gold_cs.clientes_segmentacao")

    total      = len(df)
    n_vip      = (df["segmento_cliente"] == "VIP").sum()
    rec_vip    = df.loc[df["segmento_cliente"] == "VIP", "receita_total"].sum()
    ticket_med = df["ticket_medio"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Total Clientes",     intbr(total),      EMERALD),    unsafe_allow_html=True)
    c2.markdown(kpi_card("Clientes VIP",       intbr(n_vip),      INDIGO),     unsafe_allow_html=True)
    c3.markdown(kpi_card("Receita VIP",        brl(rec_vip),      "#8B5CF6"),  unsafe_allow_html=True)
    c4.markdown(kpi_card("Ticket Médio Geral", brl(ticket_med),   AMBER),      unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    df_seg = df.groupby("segmento_cliente").size().reset_index(name="total")
    fig1 = px.pie(df_seg, names="segmento_cliente", values="total", hole=0.45,
                  title="Distribuição de Clientes por Segmento",
                  color="segmento_cliente", color_discrete_map=SEG_COLORS)
    fig1.update_traces(
        textfont=dict(size=12),
        marker=dict(line=dict(color="white", width=2)),
    )
    col1.plotly_chart(chart_theme(fig1, INDIGO), width="stretch")

    df_rec = df.groupby("segmento_cliente", as_index=False)["receita_total"].sum()
    fig2 = px.bar(df_rec, x="segmento_cliente", y="receita_total",
                  title="Receita por Segmento",
                  labels={"segmento_cliente": "Segmento", "receita_total": "Receita (R$)"},
                  color="segmento_cliente", color_discrete_map=SEG_COLORS)
    fig2.update_traces(marker_line_width=0)
    fig2.update_layout(showlegend=False)
    col2.plotly_chart(chart_theme(fig2, INDIGO), width="stretch")

    col3, col4 = st.columns(2)

    df_top = df.nsmallest(10, "ranking_receita").sort_values("receita_total")
    fig3 = px.bar(df_top, x="receita_total", y="nome_cliente", orientation="h",
                  title="Top 10 Clientes por Receita",
                  labels={"receita_total": "Receita (R$)", "nome_cliente": "Cliente"})
    fig3.update_traces(marker_color=EMERALD, marker_line_width=0)
    col3.plotly_chart(chart_theme(fig3, EMERALD), width="stretch")

    df_est = (df.groupby("estado").size().reset_index(name="total")
                .sort_values("total", ascending=False))
    fig4 = px.bar(df_est, x="estado", y="total", title="Clientes por Estado",
                  labels={"estado": "Estado", "total": "Nº de Clientes"})
    fig4.update_traces(marker_color=EMERALD, marker_line_width=0)
    col4.plotly_chart(chart_theme(fig4, EMERALD), width="stretch")

    section_label("Detalhe de Clientes")
    seg_sel = st.selectbox("Filtrar por segmento", ["Todos", "VIP", "TOP_TIER", "REGULAR"])
    df_tab = df if seg_sel == "Todos" else df[df["segmento_cliente"] == seg_sel]
    st.dataframe(df_tab, width="stretch")


# ─── Página: Pricing ──────────────────────────────────────────────────────────

def page_pricing():
    page_header("Pricing", "Competitividade de preços vs Mercado Livre, Amazon, Shopee e Magalu", AMBER)

    df = query_df("SELECT * FROM public_gold_pricing.precos_competitividade")

    cats     = sorted(df["categoria"].unique().tolist())
    sel_cats = st.multiselect("Categorias", cats, default=cats)
    if sel_cats:
        df = df[df["categoria"].isin(sel_cats)]

    total_prod = len(df)
    n_caros    = (df["classificacao_preco"] == "MAIS_CARO_QUE_TODOS").sum()
    n_baratos  = (df["classificacao_preco"] == "MAIS_BARATO_QUE_TODOS").sum()
    dif_med    = df["diferenca_percentual_vs_media"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Produtos Monitorados",   intbr(total_prod), AMBER),     unsafe_allow_html=True)
    c2.markdown(kpi_card("Mais Caros que Todos",   intbr(n_caros),    "#EF4444"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Mais Baratos que Todos", intbr(n_baratos),  EMERALD),   unsafe_allow_html=True)
    c4.markdown(kpi_card("Dif. Média vs Mercado",  pct(dif_med),      INDIGO),    unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    df_cl = df.groupby("classificacao_preco").size().reset_index(name="total")
    fig1 = px.pie(df_cl, names="classificacao_preco", values="total", hole=0.45,
                  title="Posicionamento de Preço vs Concorrência",
                  color="classificacao_preco", color_discrete_map=PRECO_COLORS)
    fig1.update_traces(
        textfont=dict(size=11),
        marker=dict(line=dict(color="white", width=2)),
    )
    col1.plotly_chart(chart_theme(fig1, AMBER), width="stretch")

    df_cat = (df.groupby("categoria", as_index=False)["diferenca_percentual_vs_media"]
                .mean().sort_values("diferenca_percentual_vs_media", ascending=False))
    fig2 = px.bar(df_cat, x="categoria", y="diferenca_percentual_vs_media",
                  title="Competitividade por Categoria",
                  labels={"categoria": "Categoria",
                          "diferenca_percentual_vs_media": "Dif. % vs Média"},
                  color="diferenca_percentual_vs_media",
                  color_continuous_scale=["#2ecc71", "#f7dc6f", "#e74c3c"])
    fig2.update_traces(marker_line_width=0)
    col2.plotly_chart(chart_theme(fig2, AMBER), width="stretch")

    fig3 = px.scatter(
        df,
        x="diferenca_percentual_vs_media",
        y="quantidade_total",
        color="classificacao_preco",
        size=df["receita_total"].clip(lower=1),
        hover_name="nome_produto",
        hover_data=["categoria", "nosso_preco"],
        title="Competitividade × Volume de Vendas",
        labels={
            "diferenca_percentual_vs_media": "Dif. % vs Média dos Concorrentes",
            "quantidade_total": "Quantidade Vendida",
            "classificacao_preco": "Classificação",
        },
        color_discrete_map=PRECO_COLORS,
    )
    st.plotly_chart(chart_theme(fig3, AMBER), width="stretch")

    section_label("Produtos em Alerta — mais caros que todos os concorrentes")
    df_alerta = (
        df.loc[
            df["classificacao_preco"] == "MAIS_CARO_QUE_TODOS",
            ["produto_id", "nome_produto", "categoria", "nosso_preco",
             "preco_maximo_concorrentes", "diferenca_percentual_vs_media"],
        ]
        .sort_values("diferenca_percentual_vs_media", ascending=False)
    )
    st.dataframe(df_alerta, width="stretch")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    inject_css()

    with st.sidebar:
        st.markdown(f"""
<div style="padding:12px 4px 8px;">
  <p style="margin:0;font-size:0.6rem;font-weight:700;color:#475569;
            letter-spacing:0.18em;text-transform:uppercase;">Analytics</p>
  <h2 style="margin:4px 0 0;font-size:1.15rem;font-weight:800;color:#FFFFFF;
             letter-spacing:-0.02em;">E-commerce</h2>
</div>
""", unsafe_allow_html=True)
        st.divider()
        pagina = st.radio(
            "Navegação",
            ["Vendas", "Clientes", "Pricing"],
            label_visibility="collapsed",
        )

    pages = {"Vendas": page_vendas, "Clientes": page_clientes, "Pricing": page_pricing}
    pages[pagina]()


if __name__ == "__main__":
    main()
