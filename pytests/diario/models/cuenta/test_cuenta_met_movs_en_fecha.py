import pytest

from diario.models import Movimiento, Cuenta
from utils.helpers_tests import dividir_en_dos_subcuentas

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures('entrada_tardia', 'traspaso_posterior')
def test_con_cuenta_interactiva_devuelve_lo_mismo_que_movs_directos_en_fecha(cuenta, fecha):
    Movimiento.crear('otro mov', 100, cuenta, fecha=fecha)
    assert (
        list(cuenta.movs_en_fecha(fecha)) ==
        list(cuenta.movs_directos_en_fecha(fecha))
    )


def test_con_cuenta_acumulativa_devuelve_movs_propios_y_de_subcuentas_en_fecha(cuenta, fecha):
    cuenta = dividir_en_dos_subcuentas(cuenta, fecha=fecha)
    sc1 = Cuenta.tomar(slug='sc1')
    mov = Movimiento.crear('mov subcuenta', 100, sc1, fecha=fecha)
    assert mov in cuenta.movs_en_fecha(fecha)
