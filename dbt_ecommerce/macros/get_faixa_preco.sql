{% macro get_faixa_preco(coluna) %}
    CASE
        WHEN {{ coluna }} > 1000 THEN 'PREMIUM'
        WHEN {{ coluna }} > 500  THEN 'MEDIO'
        ELSE 'BASICO'
    END
{% endmacro %}
