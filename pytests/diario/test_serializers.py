import pytest

from vvmodel.serializers import SerializedDb

from diario.serializers import MovimientoSerializado


@pytest.fixture
def mov_serializado(entrada, db_serializada: SerializedDb) -> MovimientoSerializado:
    return MovimientoSerializado(
        next(x for x in db_serializada if x.model == "diario.movimiento"),
        container=db_serializada
    )


class TestMovimientoSerializado:
    def test_prop_fecha_devuelve_fecha_del_dia_del_movimiento(self, mov_serializado):
        dias_serializados = [x for x in mov_serializado.container if x.model == "diario.dia"]
        assert mov_serializado.fecha == next(
            d.fields['fecha'] for d in dias_serializados
            if d.pk == mov_serializado.fields['dia']
        )
