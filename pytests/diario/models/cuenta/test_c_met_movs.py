import pytest

from diario.models import Movimiento, Cuenta, CuentaInteractiva


def test_devuelve_todos_los_movimientos_de_una_cuenta(cuenta, entrada, traspaso_posterior, entrada_tardia):
    for mov in (entrada, traspaso_posterior, entrada_tardia):
        assert mov in cuenta.movs()


def test_incluye_movimientos_de_subcuentas(cuenta: CuentaInteractiva):
    sc11, sc12 = cuenta.dividir_entre(
        {'nombre': 'subcuenta 1', 'slug': 'sc1', 'saldo': 30, },
        {'nombre': 'subcuenta 2', 'slug': 'sc2', }
    )
    cuenta = cuenta.tomar_del_slug()
    mov_subcuenta = Movimiento.crear(
        concepto='movsubc', importe=10, cta_salida=sc11)

    assert mov_subcuenta in cuenta.movs()

    subsubctas = Cuenta.tomar(slug='sc1').dividir_entre(
        {'nombre': 'subsubcuenta 1.1', 'slug': 'eb1', 'saldo': 15},
        {'nombre': 'subsubcuenta 1.2', 'slug': 'eb2', },
    )
    mov_subsubc = Movimiento.crear(
        concepto='movsubsub', importe=5, cta_salida=subsubctas[1])

    assert mov_subsubc in cuenta.movs()


def test_devuelve_movimientos_ordenados_por_fecha(cuenta, traspaso_posterior, entrada, entrada_tardia):
    assert list(cuenta.movs()) == [entrada, traspaso_posterior, entrada_tardia]
