{{
    config(
        materialized='ephemeral'
    )
}}

SELECT
    id_produto,
    SUM(receita_total)  AS receita_total,
    SUM(quantidade)     AS quantidade_total
FROM {{ ref('silver_vendas') }}
GROUP BY 1
