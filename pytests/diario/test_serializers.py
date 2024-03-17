import pytest

from diario.models import Movimiento, Dia
from vvmodel.serializers import SerializedDb

from diario.serializers import DiaSerializado, MovimientoSerializado


@pytest.fixture
def mov_serializado(entrada: Movimiento, db_serializada: SerializedDb) -> MovimientoSerializado:
    return MovimientoSerializado(next(x for x in db_serializada if x.model == "diario.movimiento"))

@pytest.fixture
def dia_serializado(dia: Dia, db_serializada: SerializedDb) -> DiaSerializado:
    return DiaSerializado(next(x for x in db_serializada if x.model == "diario.dia"))


class TestMovimientoSerializado:
    def test_prop_fecha_devuelve_fecha_del_dia_del_movimiento(self, mov_serializado):
        dias_serializados = [x for x in mov_serializado.container if x.model == "diario.dia"]
        assert mov_serializado.fecha == next(
            d.fields['fecha'] for d in dias_serializados
            if d.pk == mov_serializado.fields['dia']
        )

    def test_prop_identidad_devuelve_cadena_con_fecha_y_orden_dia(self, mov_serializado):
        assert mov_serializado.identidad == f"{mov_serializado.fecha.replace('-', '')}{mov_serializado.fields['orden_dia']:02d}"


class TestDiaSerializado:
    def test_prop_identidad_devuelve_identidad_basada_en_fecha(self, dia_serializado):
        assert dia_serializado.identidad == dia_serializado.fields["fecha"].replace('-', '')
