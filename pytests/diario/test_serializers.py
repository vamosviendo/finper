import pytest

from diario.models import CuentaAcumulativa, CuentaInteractiva, Movimiento, Dia, Saldo
from vvmodel.serializers import SerializedDb

from diario.serializers import CuentaSerializada, DiaSerializado, MovimientoSerializado, SaldoSerializado


@pytest.fixture
def cuenta_int_serializada(cuenta: CuentaInteractiva, db_serializada: SerializedDb) -> CuentaSerializada:
    return CuentaSerializada.primere(db_serializada)

@pytest.fixture
def cuenta_acum_serializada(cuenta_acumulativa: CuentaAcumulativa, db_serializada: SerializedDb) -> CuentaSerializada:
    return CuentaSerializada.primere(db_serializada)


@pytest.fixture
def mov_serializado(entrada: Movimiento, db_serializada: SerializedDb) -> MovimientoSerializado:
    return MovimientoSerializado.primere(db_serializada)

@pytest.fixture
def dia_serializado(dia: Dia, db_serializada: SerializedDb) -> DiaSerializado:
    return DiaSerializado.primere(db_serializada)

@pytest.fixture
def saldo_serializado(saldo: Saldo, db_serializada: SerializedDb) -> SaldoSerializado:
    return SaldoSerializado.primere(db_serializada)


class TestCuentaSerializada:
    def test_campos_polimorficos_devuelve_campos_de_cuenta_interactiva_correspondiente_a_cuenta(
            self, cuenta_int_serializada, ):
        assert \
            cuenta_int_serializada.campos_polimorficos() == \
            cuenta_int_serializada.container.tomar(
                model="diario.cuentainteractiva",
                pk=cuenta_int_serializada.pk
            ).fields

    def test_campos_polimorficos_devuelve_campos_de_cuenta_acumulativa_correspondiente_a_cuenta(
            self, cuenta_acum_serializada):
        assert \
            cuenta_acum_serializada.campos_polimorficos() == \
            cuenta_acum_serializada.container.tomar(
                model="diario.cuentaacumulativa",
                pk=cuenta_acum_serializada.pk
            ).fields

    def test_titname_devuelve_titname_de_titular_de_cuenta_interactiva(self, cuenta_int_serializada):
        assert \
            cuenta_int_serializada.titname() == \
            cuenta_int_serializada.campos_polimorficos()["titular"][0]

    def test_titname_devuelve_titname_de_titular_de_cuenta_acumulactiva(self, cuenta_acum_serializada):
        assert \
            cuenta_acum_serializada.titname() == \
            cuenta_acum_serializada.campos_polimorficos()["titular_original"][0]


class TestMovimientoSerializado:
    def test_prop_fecha_devuelve_fecha_del_dia_del_movimiento(self, mov_serializado):
        assert mov_serializado.fecha == mov_serializado.fields["dia"][0]

    def test_prop_identidad_devuelve_cadena_con_fecha_y_orden_dia(self, mov_serializado):
        assert mov_serializado.identidad == f"{mov_serializado.fecha.replace('-', '')}{mov_serializado.fields['orden_dia']:02d}"


class TestDiaSerializado:
    def test_prop_identidad_devuelve_identidad_basada_en_fecha(self, dia_serializado):
        assert dia_serializado.identidad == dia_serializado.fields["fecha"].replace('-', '')


class TestSaldoSerializado:
    def test_prop_identidad_devuelve_identidad_basada_en_identidad_de_movimiento_y_slug_de_cuenta(self, saldo_serializado):
        assert saldo_serializado.identidad == "2010111200c"
