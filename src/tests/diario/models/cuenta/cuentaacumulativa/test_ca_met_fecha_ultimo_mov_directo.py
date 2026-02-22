from diario.models import Movimiento, CuentaAcumulativa


def test_devuelve_fecha_de_ultimo_mov_directo(
        cuenta, entrada, traspaso_posterior, entrada_tardia, entrada_posterior_otra_cuenta,
        fecha_tardia, fecha_tardia_plus):
    subcuenta1 = cuenta.dividir_entre(
        ['subcuenta1', 'sc1', 100],
        ['subcuenta2', 'sc2'],
        fecha=fecha_tardia
    )[0]
    cuenta = CuentaAcumulativa.tomar(sk=cuenta.sk)

    Movimiento.crear(
        'cuarto movimiento', 100, subcuenta1, fecha=fecha_tardia_plus)

    assert cuenta.fecha_ultimo_mov_directo() == fecha_tardia


def test_devuelve_none_si_no_hay_movimientos_directos(cuenta_acumulativa_saldo_0):
    assert cuenta_acumulativa_saldo_0.fecha_ultimo_mov_directo() is None
