import pytest

from diario.models import CuentaInteractiva, Movimiento


def test_devuelve_todos_los_movimientos_de_una_cuenta(cuenta, entrada, traspaso_posterior, entrada_tardia):
    movs_directos = cuenta.movs_directos()
    assert len(movs_directos) == 3
    for mov in (entrada, traspaso_posterior, entrada_tardia):
        assert mov in movs_directos


def test_no_incluye_movimientos_de_otra_cuenta(cuenta, entrada_posterior_otra_cuenta):
    assert entrada_posterior_otra_cuenta not in cuenta.movs_directos()


def test_no_incluye_los_movimientos_de_subcuentas(cuenta: CuentaInteractiva):
    subcuentas = cuenta.dividir_entre(
        {'nombre': 'subcuenta 1', 'slug': 'sc1', 'saldo': 30, },
        {'nombre': 'subcuenta 2', 'slug': 'sc2', }
    )
    cuenta = cuenta.tomar_del_slug()
    mov_subcuenta = Movimiento.crear(
        concepto='movsubc', importe=10, cta_salida=subcuentas[0])

    assert mov_subcuenta not in cuenta.movs_directos()
