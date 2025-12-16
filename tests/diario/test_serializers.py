import pytest

from diario.models import CuentaAcumulativa, CuentaInteractiva, Movimiento, Dia, Moneda, SaldoDiario, \
    Titular, Cotizacion, Cuenta
from vvmodel.serializers import SerializedDb

from diario.serializers import CuentaSerializada, DiaSerializado, MovimientoSerializado, SaldoDiarioSerializado, \
    MonedaSerializada, TitularSerializado, CotizacionSerializada


# Fixtures

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
def salida_serializada(salida: Movimiento, db_serializada: SerializedDb) -> MovimientoSerializado:
    return MovimientoSerializado.primere(db_serializada)

@pytest.fixture
def traspaso_serializado(traspaso: Movimiento, db_serializada: SerializedDb) -> MovimientoSerializado:
    return MovimientoSerializado.primere(db_serializada)

@pytest.fixture
def dia_serializado(dia: Dia, db_serializada: SerializedDb) -> DiaSerializado:
    return DiaSerializado.primere(db_serializada)

@pytest.fixture
def saldo_serializado(saldo_diario: SaldoDiario, db_serializada: SerializedDb) -> SaldoDiarioSerializado:
    return SaldoDiarioSerializado.primere(db_serializada)

@pytest.fixture
def moneda_serializada(dolar: Moneda, db_serializada: SerializedDb) -> MonedaSerializada:
    return MonedaSerializada.primere(db_serializada)

@pytest.fixture
def titular_serializado(titular: Titular, db_serializada: SerializedDb) -> TitularSerializado:
    return TitularSerializado.primere(db_serializada)

@pytest.fixture
def cotizacion_serializada(cotizacion_dolar: Cotizacion, db_serializada: SerializedDb) -> CotizacionSerializada:
    return CotizacionSerializada.primere(db_serializada)


# Tests

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

    def test_sk_tit_devuelve_sk_de_titular_de_cuenta_interactiva(self, cuenta_int_serializada):
        assert \
            cuenta_int_serializada.sk_tit() == \
            cuenta_int_serializada.campos_polimorficos()["titular"][0]

    def test_sk_tit_devuelve_sk_de_titular_de_cuenta_acumulactiva(self, cuenta_acum_serializada):
        assert \
            cuenta_acum_serializada.sk_tit() == \
            cuenta_acum_serializada.campos_polimorficos()["titular_original"][0]

    def test_es_cuenta_credito_devuelve_True_si_la_cuenta_es_cuenta_credito(self, credito, db_serializada):
        cuentas = CuentaSerializada.todes(db_serializada)
        for cta in cuentas:
            print(cta)
        cuenta_credito = CuentaSerializada(cuentas.tomar(sk="_otro-titular"))
        cuenta_credito_2 = CuentaSerializada(cuentas.tomar(sk="_titular-otro"))
        assert cuenta_credito.es_cuenta_credito() is True
        assert cuenta_credito_2.es_cuenta_credito() is True

    def test_es_cuenta_credito_devuelve_False_si_la_cuenta_no_es_cuenta_credito(self, credito, db_serializada):
        cuentas = CuentaSerializada.todes(db_serializada)
        cuenta_credito = CuentaSerializada(cuentas.tomar(sk="caj"))
        assert cuenta_credito.es_cuenta_credito() is False

    def test_es_subcuenta_de_devuelve_True_si_la_cuenta_es_subcuenta_de_otra_cuenta(
            self, cuenta_acum_serializada, db_serializada):
        subcuentas = SerializedDb([
            CuentaSerializada(x) for x in db_serializada.filter_by_model("diario.cuenta")
            if x.fields["cta_madre"] == [cuenta_acum_serializada.sk]
        ])
        assert len(subcuentas) > 0
        for subcuenta in subcuentas:
            assert subcuenta.es_subcuenta_de(cuenta_acum_serializada) is True

    def test_es_subcuenta_de_devuelve_False_si_la_cuenta_no_es_subcuenta_de_otra_cuenta(
            self, cuenta_acum_serializada, cuenta_int_serializada):
        assert cuenta_int_serializada.es_subcuenta_de(cuenta_acum_serializada) is False


class TestMovimientoSerializado:
    def test_prop_fecha_devuelve_fecha_del_dia_del_movimiento(self, mov_serializado):
        assert mov_serializado.fecha == mov_serializado.fields["dia"][0]

    def test_prop_sk_devuelve_cadena_con_fecha_y_orden_dia(self, mov_serializado):
        assert mov_serializado.sk == f"{mov_serializado.fecha.replace('-', '')}{mov_serializado.fields['orden_dia']:02d}"

    @pytest.mark.parametrize("mov", ["mov_serializado", "salida_serializada"])
    def test_met_es_entrada_o_salida_devuelve_true_si_es_entrada_o_salida(self, mov, request):
        movimiento = request.getfixturevalue(mov)
        assert movimiento.es_entrada_o_salida() is True

    def test_met_es_entrada_o_salida_devuelve_false_si_es_traspaso(self, traspaso_serializado):
        assert traspaso_serializado.es_entrada_o_salida() is False


class TestDiaSerializado:
    def test_prop_sk_devuelve_cadena_con_fecha_formateada_como_numero(self, dia_serializado):
        assert dia_serializado.sk == dia_serializado.fields["fecha"].replace('-', '')


class TestSaldoDiarioSerializado:
    def test_prop_sk_devuelve_cadena_con_sk_de_dia_y_sk_de_cuenta(self, saldo_serializado):
        dia = Dia.tomar(fecha=saldo_serializado.fields["dia"][0])
        cuenta = Cuenta.tomar(saldo_serializado.fields['cuenta'][0])
        assert saldo_serializado.sk == f"{dia.sk}{cuenta.sk}"


class TestCotizacionSerializada:
    def test_prop_sk_devuelve_cadena_con_fecha_formateada_como_numero_y_sk_de_moneda(self, cotizacion_serializada):
        assert \
            cotizacion_serializada.sk == \
            cotizacion_serializada.fields["fecha"].replace("-", "") +  cotizacion_serializada.fields["moneda"][0]


@pytest.mark.parametrize("fixt_obj", ["cuenta_int_serializada", "moneda_serializada", "titular_serializado"])
class TestSkSimpleMixin:
    def test_prop_sk_devuelve_contenido_del_campo_sk(self, fixt_obj, request):
        obj = request.getfixturevalue(fixt_obj)
        assert obj.sk == obj.fields["sk"]

    def test_prop_sk_permite_fijar_contenido_del_campo_sk(self, fixt_obj, request):
        obj = request.getfixturevalue(fixt_obj)
        obj.sk = "ccc"
        assert obj.fields["sk"] == "ccc"
