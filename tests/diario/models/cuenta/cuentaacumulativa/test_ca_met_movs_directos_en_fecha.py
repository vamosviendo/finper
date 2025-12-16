from diario.models import Movimiento, Cuenta
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_devuelve_movs_directos_de_cuenta_en_fecha(cuenta, dia):
    cuenta = dividir_en_dos_subcuentas(cuenta, fecha=dia.fecha)
    sc1 = Cuenta.tomar(sk='sc1')
    mov = Movimiento.crear('mov subcuenta', 100, sc1, dia=dia)

    assert mov not in cuenta.movs_directos_en_fecha(dia)
