{% snapshot snapshot_preco_competidores %}

{{
    config(
        target_schema='snapshots',
        unique_key="id_produto || '|' || nome_concorrente",
        strategy='check',
        check_cols=['preco_concorrente']
    )
}}

SELECT
    id_produto,
    nome_concorrente,
    preco_concorrente,
    data_coleta
FROM {{ source('raw', 'preco_competidores') }}

{% endsnapshot %}
