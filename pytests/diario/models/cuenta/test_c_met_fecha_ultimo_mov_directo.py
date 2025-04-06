import pytest

from diario.models import CuentaInteractiva, Movimiento


@pytest.mark.usefixtures(
    'entrada',
    'traspaso_posterior',
    'entrada_tardia',
    'entrada_posterior_otra_cuenta')
def test_devuelve_fecha_ultimo_movimiento(cuenta, fecha_tardia):
    assert cuenta.fecha_ultimo_mov_directo() == fecha_tardia


def test__devuelve_none_si_no_hay_movimientos(cuenta):
    assert cuenta.fecha_ultimo_mov_directo() is None


@pytest.mark.usefixtures(
    'entrada',
    'traspaso_posterior',
    'entrada_tardia',
    'entrada_posterior_otra_cuenta')
def test_en_cta_acumulativa_devuelve_ultimo_mov_directo(cuenta: CuentaInteractiva, fecha_tardia, fecha_tardia_plus):
    subcuenta1 = cuenta.dividir_entre(
        ['subcuenta1', 'sc1', 100],
        ['subcuenta2', 'sc2'],
        fecha=fecha_tardia
    )[0]
    cuenta = cuenta.tomar_del_sk()

    Movimiento.crear(
        'cuarto movimiento', 100, subcuenta1, fecha=fecha_tardia_plus)

    assert cuenta.fecha_ultimo_mov_directo() == fecha_tardia
