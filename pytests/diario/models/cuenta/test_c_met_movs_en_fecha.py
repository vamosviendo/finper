import pytest

from diario.models import Movimiento, Cuenta
from utils.helpers_tests import dividir_en_dos_subcuentas


@pytest.mark.usefixtures('entrada_tardia', 'traspaso_posterior')
def test_con_cuenta_interactiva_devuelve_lo_mismo_que_movs_directos_en_fecha(cuenta, dia):
    Movimiento.crear('otro mov', 100, cuenta, dia=dia)
    assert (
        list(cuenta.movs_en_fecha(dia)) ==
        list(cuenta.movs_directos_en_fecha(dia))
    )


def test_con_cuenta_acumulativa_devuelve_movs_propios_y_de_subcuentas_en_fecha(cuenta, dia):
    cuenta = dividir_en_dos_subcuentas(cuenta, fecha=dia.fecha)
    sc1 = Cuenta.tomar(sk='sc1')
    mov = Movimiento.crear('mov subcuenta', 100, sc1, dia=dia)
    assert mov in cuenta.movs_en_fecha(dia)
