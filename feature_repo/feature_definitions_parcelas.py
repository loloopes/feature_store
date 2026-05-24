from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float64, Int64, String
from feast.value_type import ValueType

parcela = Entity(
    name="parcela",
    join_keys=["id_contrato"],
    value_type=ValueType.INT64,
)

parcelas_source = FileSource(
    name="historico_parcelas",
    path="data/historico_parcelas.parquet",
    timestamp_field="data_prevista_pagamento",
)

historico_parcelas_fv = FeatureView(
    name="historico_parcelas",
    entities=[parcela],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="id_cliente", dtype=Int64),
        Field(name="numero_parcela", dtype=Int64),
        Field(name="versao_parcela", dtype=Float64),
        Field(name="data_real_pagamento", dtype=String),
        Field(name="valor_previsto_parcela", dtype=Float64),
        Field(name="valor_pago_parcela", dtype=Float64),
    ],
    online=False,
    source=parcelas_source,
    tags={"team": "credit", "visibility": "internal"},
)
