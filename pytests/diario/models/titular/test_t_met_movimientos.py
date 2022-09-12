from diario.models import CuentaInteractiva, Movimiento
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_devuelve_solo_movimientos_relacionados_con_cuentas_del_titular(
        titular, entrada, salida, entrada_cuenta_ajena, donacion):
    for mov in (entrada, salida, donacion):
        assert mov in titular.movimientos()
    assert entrada_cuenta_ajena not in titular.movimientos()


def test_incluye_movimientos_de_cuentas_convertidas_en_acumulativas(titular, cuenta, entrada):
    dividir_en_dos_subcuentas(cuenta, saldo=15)
    assert entrada in titular.movimientos()


def test_incluye_una_sola_vez_traspaso_entre_cuentas_del_mismo_titular(titular, traspaso):
    assert len(titular.movimientos()) == 1


def test_no_incluye_movimientos_de_subcuentas_de_otro_titular_de_cuentas_que_eran_del_titular_originalmente(
        titular, cuenta, otro_titular):
    sc_ajena, sc_propia = cuenta.dividir_entre(
        {
            'nombre': 'subcuenta ajena',
            'slug': 'scaj',
            'saldo': 30,
            'titular': otro_titular
        },
        {'nombre': 'subcuenta propia', 'slug': 'scpr'},
    )
    mov_sc_propia = Movimiento.crear(
        concepto='Movimiento de subcuenta propia',
        importe=50,
        cta_entrada=sc_propia
    )
    mov_sc_ajena = Movimiento.crear(
        concepto='Movimiento de subcuenta de otro titular '
                 'de cuenta que era mía',
        importe=10,
        cta_salida=sc_ajena
    )

    assert mov_sc_propia in titular.movimientos()
    assert mov_sc_ajena not in titular.movimientos()


def test_devuelve_movimientos_ordenados_por_fecha(
        titular, salida_posterior, entrada_tardia, entrada, entrada_anterior):
    assert \
        titular.movimientos() == \
        [entrada_anterior, entrada, salida_posterior, entrada_tardia]


def test_dentro_de_la_fecha_ordena_los_movimientos_por_orden_dia(
        titular, entrada, salida, traspaso):
    traspaso.orden_dia = 1
    traspaso.save()

    assert titular.movimientos() == [entrada, traspaso, salida]

