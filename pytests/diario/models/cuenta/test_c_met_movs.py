from diario.models import Movimiento, Cuenta, CuentaInteractiva


def test_devuelve_todos_los_movimientos_de_una_cuenta(cuenta, entrada, traspaso_posterior, entrada_tardia):
    for mov in (entrada, traspaso_posterior, entrada_tardia):
        assert mov in cuenta.movs()


def test_no_incluye_movimientos_que_no_sean_de_la_cuenta(cuenta, entrada, entrada_otra_cuenta, entrada_tardia):
    assert entrada_otra_cuenta not in cuenta.movs()


def test_incluye_movimientos_de_subcuentas(cuenta: CuentaInteractiva):
    sc11, sc12 = cuenta.dividir_entre(
        {'nombre': 'subcuenta 1', 'sk': 'sc1', 'saldo': 30, },
        {'nombre': 'subcuenta 2', 'sk': 'sc2', }
    )
    cuenta = cuenta.tomar_del_sk()
    mov_subcuenta = Movimiento.crear(
        concepto='movsubc', importe=10, cta_salida=sc11)

    assert mov_subcuenta in cuenta.movs()

    subsubctas = Cuenta.tomar(sk='sc1').dividir_entre(
        {'nombre': 'subsubcuenta 1.1', 'sk': 'eb1', 'saldo': 15},
        {'nombre': 'subsubcuenta 1.2', 'sk': 'eb2', },
    )
    mov_subsubc = Movimiento.crear(
        concepto='movsubsub', importe=5, cta_salida=subsubctas[1])

    assert mov_subsubc in cuenta.movs()


def test_devuelve_movimientos_ordenados_por_fecha_y_orden_dia(cuenta, traspaso_posterior, entrada, salida, entrada_tardia):
    entrada.orden_dia = 1
    entrada.save()
    salida.refresh_from_db()

    assert list(cuenta.movs()) == [salida, entrada, traspaso_posterior, entrada_tardia]
