import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

import anthropic
from dotenv import load_dotenv

from db import execute_query

load_dotenv()

MODEL = "claude-sonnet-4-6"

TOOL_EXECUTAR_SQL = {
    "name": "executar_sql",
    "description": "Executa query SQL SELECT no banco PostgreSQL do e-commerce.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "Query SQL SELECT para executar.",
            }
        },
        "required": ["sql"],
    },
}

_SCHEMA = """
Schema do banco PostgreSQL:

**public_gold_sales.vendas_temporais** (granularidade: data_venda + hora_venda)
Colunas: data_venda DATE, ano_venda INT, mes_venda INT, dia_venda INT,
dia_semana_nome VARCHAR ('Domingo'/'Segunda'/'Terca'/'Quarta'/'Quinta'/'Sexta'/'Sabado'),
hora_venda INT, receita_total NUMERIC, quantidade_total INT,
total_vendas INT, total_clientes_unicos INT, ticket_medio NUMERIC

**public_gold_cs.clientes_segmentacao** (granularidade: cliente_id)
Colunas: cliente_id VARCHAR, nome_cliente VARCHAR, estado VARCHAR,
receita_total NUMERIC, total_compras INT, ticket_medio NUMERIC,
primeira_compra DATE, ultima_compra DATE,
segmento_cliente VARCHAR ('VIP'/'TOP_TIER'/'REGULAR'), ranking_receita INT
Segmentação: VIP ≥ R$10.000 | TOP_TIER ≥ R$5.000 | REGULAR < R$5.000

**public_gold_pricing.precos_competitividade** (granularidade: produto_id)
Colunas: produto_id VARCHAR, nome_produto VARCHAR, categoria VARCHAR, marca VARCHAR,
nosso_preco NUMERIC, preco_medio_concorrentes NUMERIC,
preco_minimo_concorrentes NUMERIC, preco_maximo_concorrentes NUMERIC,
total_concorrentes INT,
diferenca_percentual_vs_media NUMERIC (positivo = mais caro que a média),
diferenca_percentual_vs_minimo NUMERIC (positivo = mais caro que o mais barato),
classificacao_preco VARCHAR ('MAIS_CARO_QUE_TODOS'/'ACIMA_DA_MEDIA'/'NA_MEDIA'
/'ABAIXO_DA_MEDIA'/'MAIS_BARATO_QUE_TODOS'),
receita_total NUMERIC, quantidade_total INT
Concorrentes monitorados: Mercado Livre, Amazon, Shopee, Magalu
"""

SYSTEM_CHAT = f"""Você é um analista de dados de um e-commerce brasileiro.
Responda perguntas usando os dados do banco PostgreSQL.
Use a ferramenta executar_sql para consultar os dados necessários.
Formate valores monetários em R$. Responda em português.
Seja conciso e direto.

{_SCHEMA}"""

SYSTEM_RELATORIO = """Você é um analista de dados senior de um e-commerce.
Sua função é gerar um relatório executivo diário para 3 diretores.
Cada diretor tem necessidades diferentes:

1. Diretor Comercial: receita, vendas, ticket médio e tendências.
2. Diretora de Customer Success: segmentação de clientes, VIPs e riscos.
3. Diretor de Pricing: posicionamento de preço vs concorrência e alertas.

Regras do relatório:
- Seja direto e acionável. Cada insight deve sugerir uma ação.
- Use números reais dos dados fornecidos.
- Formate valores monetários em reais (R$).
- Destaque alertas críticos no início.
- O relatório deve ter no máximo 1 página por diretor.
- Use formato Markdown."""

_QUERY_VENDAS = """
SELECT data_venda, dia_semana_nome,
    SUM(receita_total) AS receita,
    SUM(total_vendas) AS vendas,
    SUM(total_clientes_unicos) AS clientes,
    AVG(ticket_medio) AS ticket_medio
FROM public_gold_sales.vendas_temporais
GROUP BY data_venda, dia_semana_nome
ORDER BY data_venda DESC
LIMIT 7
"""

_QUERY_CLIENTES = """
SELECT segmento_cliente,
    COUNT(*) AS total_clientes,
    SUM(receita_total) AS receita_total,
    AVG(ticket_medio) AS ticket_medio_avg,
    AVG(total_compras) AS compras_avg
FROM public_gold_cs.clientes_segmentacao
GROUP BY segmento_cliente
ORDER BY receita_total DESC
"""

_QUERY_PRICING = """
SELECT classificacao_preco,
    COUNT(*) AS total_produtos,
    AVG(diferenca_percentual_vs_media) AS dif_media_pct,
    SUM(receita_total) AS receita_impactada
FROM public_gold_pricing.precos_competitividade
GROUP BY classificacao_preco
ORDER BY total_produtos DESC
"""

_QUERY_PRODUTOS_CRITICOS = """
SELECT nome_produto, categoria, nosso_preco,
    preco_medio_concorrentes,
    diferenca_percentual_vs_media,
    receita_total
FROM public_gold_pricing.precos_competitividade
WHERE classificacao_preco = 'MAIS_CARO_QUE_TODOS'
ORDER BY diferenca_percentual_vs_media DESC
LIMIT 10
"""


def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def chat(pergunta: str, historico: list = None) -> str:
    client = anthropic.Anthropic()

    if historico is None:
        historico = []

    messages = list(historico) + [{"role": "user", "content": pergunta}]

    for _ in range(10):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_CHAT,
            tools=[TOOL_EXECUTAR_SQL],
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    try:
                        df = execute_query(block.input["sql"])
                        result = (
                            df.to_markdown(index=False)
                            if not df.empty
                            else "Nenhum resultado encontrado."
                        )
                    except Exception as e:
                        result = f"Erro ao executar SQL: {e}"
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )

            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "Não foi possível gerar uma resposta após o limite de iterações."


def gerar_relatorio() -> str:
    _log("Iniciando geração do relatório...")
    client = anthropic.Anthropic()

    try:
        _log("Consultando vendas...")
        df_vendas = execute_query(_QUERY_VENDAS)

        _log("Consultando clientes...")
        df_clientes = execute_query(_QUERY_CLIENTES)

        _log("Consultando pricing...")
        df_pricing = execute_query(_QUERY_PRICING)

        _log("Consultando produtos_criticos...")
        df_criticos = execute_query(_QUERY_PRODUTOS_CRITICOS)
    except Exception as e:
        return f"Erro ao consultar banco de dados: {e}"

    user_prompt = f"""Gere o relatório diário com base nos dados abaixo.

## Dados de Vendas (últimos 7 dias)
{df_vendas.to_markdown(index=False)}

## Segmentação de Clientes
{df_clientes.to_markdown(index=False)}

## Posicionamento de Preços
{df_pricing.to_markdown(index=False)}

## Produtos Críticos (mais caros que todos os concorrentes)
{df_criticos.to_markdown(index=False)}

Gere o relatório com 3 seções:
1. Comercial (para o Diretor Comercial)
2. Customer Success (para a Diretora de CS)
3. Pricing (para o Diretor de Pricing)

Comece com um resumo executivo de 3 linhas antes das seções."""

    _log("Enviando para Claude API...")

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_RELATORIO,
            messages=[{"role": "user", "content": user_prompt}],
        )
        relatorio = response.content[0].text
    except Exception as e:
        data = datetime.now().strftime("%d/%m/%Y")
        relatorio = (
            f"# Relatório Diário - E-commerce\nData: {data}\n\n"
            f"*Erro na API Claude: {e}*\n\n"
            f"## Dados Brutos\n\n"
            f"### Vendas\n{df_vendas.to_markdown(index=False)}\n\n"
            f"### Clientes\n{df_clientes.to_markdown(index=False)}\n\n"
            f"### Pricing\n{df_pricing.to_markdown(index=False)}\n\n"
            f"### Produtos Críticos\n{df_criticos.to_markdown(index=False)}"
        )

    filename = f"relatorio_{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(relatorio)
    _log(f"Relatório salvo em: {filename}")

    return relatorio


def _enviar_chunk(token: str, chat_id: str, texto: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"}
    ).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                _log(f"Mensagem enviada para chat_id={chat_id}")
                return
    except Exception:
        pass

    # Fallback: texto puro
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": texto}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                _log(f"Mensagem enviada (texto puro) para chat_id={chat_id}")
            else:
                _log(f"Erro ao enviar mensagem: {result}")
    except Exception as e:
        _log(f"Erro ao enviar mensagem Telegram: {e}")


def enviar_telegram(texto: str, chat_id: str = None):
    token = os.getenv("TELEGRAM")
    if not token:
        _log("TELEGRAM token não configurado no .env")
        return

    if chat_id is None:
        chat_id = os.getenv("CHAT_ID")

    if not chat_id:
        _log("CHAT_ID não configurado. Rode o bot primeiro e envie /start.")
        return

    chunks = [texto[i : i + 4096] for i in range(0, len(texto), 4096)]
    for chunk in chunks:
        _enviar_chunk(token, str(chat_id), chunk)


if __name__ == "__main__":
    relatorio = gerar_relatorio()
    print("\n" + relatorio)

    chat_id = os.getenv("CHAT_ID")
    if chat_id:
        enviar_telegram(relatorio, chat_id)
    else:
        _log(
            "CHAT_ID não configurado. "
            "Para enviar ao Telegram, rode o bot primeiro e envie /start."
        )
