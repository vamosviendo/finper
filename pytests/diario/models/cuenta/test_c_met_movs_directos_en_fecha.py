import pytest

from diario.models import Movimiento, Cuenta
from utils.helpers_tests import dividir_en_dos_subcuentas


@pytest.mark.usefixtures('entrada_tardia', 'traspaso_posterior')
def test_con_cuenta_interactiva_devuelve_movs_de_cuenta_en_fecha(cuenta, entrada, dia):
    mov = Movimiento.crear('otro mov', 100, cuenta, dia=dia)
    assert (
        list(cuenta.movs_directos_en_fecha(dia)) == [entrada, mov]
    )


def test_con_cuenta_acumulativa_devuelve_solo_movs_directos_de_cuenta_en_fecha(cuenta, dia):
    cuenta = dividir_en_dos_subcuentas(cuenta, fecha=dia.fecha)
    sc1 = Cuenta.tomar(sk='sc1')
    mov = Movimiento.crear('mov subcuenta', 100, sc1, dia=dia)

    assert mov not in cuenta.movs_directos_en_fecha(dia)
