{% macro get_segmento_cliente(coluna_receita) %}
    CASE
        WHEN {{ coluna_receita }} >= {{ var('segmentacao_vip_threshold', 10000) }}     THEN 'VIP'
        WHEN {{ coluna_receita }} >= {{ var('segmentacao_top_tier_threshold', 5000) }} THEN 'TOP_TIER'
        ELSE 'REGULAR'
    END
{% endmacro %}
