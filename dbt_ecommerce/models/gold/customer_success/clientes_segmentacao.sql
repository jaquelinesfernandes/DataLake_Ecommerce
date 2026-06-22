SELECT
    id_cliente AS cliente_id,
    nome_cliente,
    estado,
    receita_total,
    total_compras,
    ticket_medio,
    primeira_compra,
    ultima_compra,
    {{ get_segmento_cliente('receita_total') }} AS segmento_cliente,
    ROW_NUMBER() OVER (ORDER BY receita_total DESC) AS ranking_receita
FROM {{ ref('int_receita_por_cliente') }}
ORDER BY receita_total DESC
