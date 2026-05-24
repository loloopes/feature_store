from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource, Project
from feast.types import Float64, Int64, String
from feast.value_type import ValueType

project = Project(
    name="correct_phoenix", description="Credit analysis forecast project"
)

emprestimo = Entity(
    name="emprestimo",
    join_keys=["id_contrato"],
    value_type=ValueType.INT64,
)

emprestimo_source = FileSource(
    name="historico_emprestimo",
    path="data/historico_emprestimos.parquet",
    timestamp_field="data_decisao",
)

historico_emprestimo_fv = FeatureView(
    name="historico_emprestimos",
    entities=[emprestimo],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="id_cliente", dtype=Int64),
        Field(name="tipo_contrato", dtype=String),
        Field(name="status_contrato", dtype=String),
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
    ],
    online=False,
    source=emprestimo_source,
    tags={"team": "credit", "visibility": "internal"},
)
