import pytest

from diario.models import CuentaInteractiva, Movimiento, CuentaAcumulativa


def test_devuelve_todos_los_movimientos_directos_de_una_cuenta_acumulativa(
        cuenta, entrada, traspaso_posterior, entrada_tardia, entrada_posterior_otra_cuenta,
        fecha_tardia):
    cuenta.dividir_entre(
        ['subcuenta1', 'sc1', 100],
        ['subcuenta2', 'sc2'],
        fecha=fecha_tardia
    )
    cuenta = CuentaAcumulativa.tomar(sk=cuenta.sk)
    movs_directos = cuenta.movs_directos()
    print(*movs_directos, sep="\n")
    assert len(movs_directos) == 5
    for mov in (entrada, traspaso_posterior, entrada_tardia):
        assert mov in movs_directos


def test_no_incluye_movimientos_de_otra_cuenta(cuenta_acumulativa, entrada_posterior_otra_cuenta):
    assert entrada_posterior_otra_cuenta not in cuenta_acumulativa.movs_directos()


def test_no_incluye_los_movimientos_de_subcuentas(cuenta: CuentaInteractiva):
    subcuentas = cuenta.dividir_entre(
        {'nombre': 'subcuenta 1', 'sk': 'sc1', 'saldo': 30, },
        {'nombre': 'subcuenta 2', 'sk': 'sc2', }
    )
    cuenta = CuentaAcumulativa.tomar(sk=cuenta.sk)
    mov_subcuenta = Movimiento.crear(
        concepto='movsubc', importe=10, cta_salida=subcuentas[0])

    assert mov_subcuenta not in cuenta.movs_directos()
