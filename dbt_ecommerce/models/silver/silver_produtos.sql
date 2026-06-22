SELECT
    id_produto,
    nome_produto,
    categoria,
    marca,
    preco_atual,
    data_criacao,
    {{ get_faixa_preco('preco_atual') }} AS faixa_preco
FROM {{ ref('bronze_produtos') }}
