from diario.models import Movimiento, Cuenta
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_con_cuenta_interactiva_devuelve_movimientos_propios_en_fecha(
        cuenta, entrada, salida, traspaso_posterior, entrada_cuenta_ajena, dia):
    assert list(cuenta.movs_en_fecha(dia)) == [entrada, salida]


def test_no_devuelve_movimientos_propios_de_otra_fecha(cuenta, entrada, traspaso_posterior, dia):
    assert traspaso_posterior not in cuenta.movs_en_fecha(dia)


def test_no_devuelve_movimientos_de_otra_cuenta_en_fecha(cuenta, entrada, entrada_otra_cuenta, dia):
    assert entrada_otra_cuenta not in cuenta.movs_en_fecha(dia)


def test_con_cuenta_acumulativa_devuelve_movs_propios_y_de_subcuentas_en_fecha(cuenta, dia):
    cuenta = dividir_en_dos_subcuentas(cuenta, fecha=dia.fecha)
    sc1 = Cuenta.tomar(sk='sc1')
    mov = Movimiento.crear('mov subcuenta', 100, sc1, dia=dia)
    assert mov in cuenta.movs_en_fecha(dia)
