"""Internal merged inputs for CreditFeatureEngineering (not served to clients)."""

from datetime import timedelta

from feast import FeatureView, Field, FileSource
from feast.types import Float64, Int64, String

from feature_definitions_emprestimos import emprestimo

credit_model_inputs_source = FileSource(
    name="credit_model_inputs",
    path="data/credit_model_inputs.parquet",
    timestamp_field="data_decisao",
)

credit_model_inputs_fv = FeatureView(
    name="credit_model_inputs",
    entities=[emprestimo],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="id_cliente", dtype=Int64),
        Field(name="tipo_contrato", dtype=String),
        Field(name="status_contrato", dtype=String),
        Field(name="data_decisao", dtype=String),
        Field(name="data_liberacao", dtype=String),
        Field(name="data_primeiro_vencimento", dtype=String),
        Field(name="data_ultimo_vencimento_original", dtype=String),
        Field(name="data_ultimo_vencimento", dtype=String),
        Field(name="data_encerramento", dtype=String),
        Field(name="valor_solicitado", dtype=Float64),
        Field(name="valor_credito", dtype=Float64),
        Field(name="valor_bem", dtype=Float64),
        Field(name="valor_parcela", dtype=Float64),
        Field(name="valor_entrada", dtype=Float64),
        Field(name="percentual_entrada", dtype=Float64),
        Field(name="qtd_parcelas_planejadas", dtype=Float64),
        Field(name="taxa_juros_padrao", dtype=Float64),
        Field(name="taxa_juros_promocional", dtype=Float64),
        Field(name="tipo_pagamento", dtype=String),
        Field(name="finalidade_emprestimo", dtype=String),
        Field(name="tipo_cliente", dtype=String),
        Field(name="faixa_rendimento", dtype=String),
        Field(name="tipo_portfolio", dtype=String),
        Field(name="tipo_produto", dtype=String),
        Field(name="categoria_bem", dtype=String),
        Field(name="combinacao_produto", dtype=String),
        Field(name="setor_vendedor", dtype=String),
        Field(name="canal_venda", dtype=String),
        Field(name="area_venda", dtype=Int64),
        Field(name="dia_semana_solicitacao", dtype=String),
        Field(name="hora_solicitacao", dtype=Int64),
        Field(name="flag_ultima_solicitacao_contrato", dtype=String),
        Field(name="flag_ultima_solicitacao_dia", dtype=Int64),
        Field(name="motivo_recusa", dtype=String),
        Field(name="acompanhantes_cliente", dtype=String),
        Field(name="flag_seguro_contratado", dtype=Float64),
        Field(name="sexo", dtype=String),
        Field(name="data_nascimento", dtype=String),
        Field(name="qtd_filhos", dtype=Int64),
        Field(name="qtd_membros_familia", dtype=Float64),
        Field(name="renda_anual", dtype=Float64),
        Field(name="tipo_renda", dtype=String),
        Field(name="ocupacao", dtype=String),
        Field(name="tipo_organizacao", dtype=String),
        Field(name="nivel_educacao", dtype=String),
        Field(name="estado_civil", dtype=String),
        Field(name="tipo_moradia", dtype=String),
        Field(name="possui_carro", dtype=String),
        Field(name="possui_imovel", dtype=String),
        Field(name="nota_regiao_cliente", dtype=Int64),
        Field(name="nota_regiao_cliente_cidade", dtype=Int64),
    ],
    online=True,
    source=credit_model_inputs_source,
    tags={"team": "credit", "visibility": "internal"},
)
