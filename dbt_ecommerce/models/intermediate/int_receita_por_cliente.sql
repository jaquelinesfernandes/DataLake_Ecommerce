{{
    config(
        materialized='ephemeral'
    )
}}

SELECT
    v.id_cliente,
    c.nome_cliente,
    c.estado,
    SUM(v.receita_total)          AS receita_total,
    COUNT(DISTINCT v.id_venda)    AS total_compras,
    AVG(v.receita_total)          AS ticket_medio,
    MIN(v.data_venda_date)        AS primeira_compra,
    MAX(v.data_venda_date)        AS ultima_compra
FROM {{ ref('silver_vendas') }} v
LEFT JOIN {{ ref('silver_clientes') }} c
    ON v.id_cliente = c.id_cliente
GROUP BY 1, 2, 3
