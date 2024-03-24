import pytest

from diario.models import Movimiento, Dia, Saldo
from vvmodel.serializers import SerializedDb

from diario.serializers import DiaSerializado, MovimientoSerializado, SaldoSerializado


@pytest.fixture
def mov_serializado(entrada: Movimiento, db_serializada: SerializedDb) -> MovimientoSerializado:
    return MovimientoSerializado.primere(db_serializada)

@pytest.fixture
def dia_serializado(dia: Dia, db_serializada: SerializedDb) -> DiaSerializado:
    return DiaSerializado.primere(db_serializada)

@pytest.fixture
def saldo_serializado(saldo: Saldo, db_serializada: SerializedDb) -> SaldoSerializado:
    return SaldoSerializado.primere(db_serializada)


class TestMovimientoSerializado:
    def test_prop_fecha_devuelve_fecha_del_dia_del_movimiento(self, mov_serializado):
        assert mov_serializado.fecha == mov_serializado.fields["dia"]

    def test_prop_identidad_devuelve_cadena_con_fecha_y_orden_dia(self, mov_serializado):
        assert mov_serializado.identidad == f"{mov_serializado.fecha.replace('-', '')}{mov_serializado.fields['orden_dia']:02d}"


class TestDiaSerializado:
    def test_prop_identidad_devuelve_identidad_basada_en_fecha(self, dia_serializado):
        assert dia_serializado.identidad == dia_serializado.fields["fecha"].replace('-', '')


class TestSaldoSerializado:
    def test_prop_identidad_devuelve_identidad_basada_en_identidad_de_movimiento_y_slug_de_cuenta(self, saldo_serializado):
        assert saldo_serializado.identidad == \
               f"{saldo_serializado.fields['movimiento']}" \
               f"{saldo_serializado.fields['cuenta']}"
