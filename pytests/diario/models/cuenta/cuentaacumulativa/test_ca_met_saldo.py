import pytest

from diario.models import Movimiento


def test_devuelve_suma_de_saldos_de_subcuentas_interactivas(cuenta_acumulativa_saldo_0, fecha):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    Movimiento.crear('saldo sc1', 100, sc1, fecha=fecha)
    Movimiento.crear('saldo sc2', 70, None, sc2, fecha=fecha)

    assert cuenta_acumulativa_saldo_0.saldo() == 100 - 70


def test_devuelve_suma_de_saldos_incluyendo_subcuentas_acumulativas(cuenta_acumulativa_saldo_0, fecha):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    Movimiento.crear('saldo sc1', 100, sc1, fecha=fecha)
    Movimiento.crear('saldo sc2', 70, None, sc2, fecha=fecha)

    sc11, sc12 = sc1.dividir_entre(
        ['subsubcuenta 1.1', 'sc11', 30],
        ['subsubcuenta 1.2', 'sc12'],
        fecha=fecha
    )
    Movimiento.crear('saldo sc11', 60, sc11, fecha=fecha)
    sc1 = sc1.tomar_del_slug()

    assert sc1.saldo() == 90 + 70
    assert cuenta_acumulativa_saldo_0.saldo() == 160 - 70


def test_si_recibe_movimiento_devuelve_saldo_al_momento_del_movimiento(
        cuenta_acumulativa, fecha_posterior, fecha_tardia):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    mov1 = Movimiento.crear('movimiento posterior sc1', 150, sc1, fecha=fecha_posterior)
    saldo_en_mov1 = cuenta_acumulativa.saldo()
    Movimiento.crear('movimiento tardío sc2', 150, sc1, fecha=fecha_tardia)

    saldo_en_mov = cuenta_acumulativa.saldo(movimiento=mov1)
    assert saldo_en_mov != cuenta_acumulativa.saldo()
    assert saldo_en_mov == saldo_en_mov1


def test_saldo_de_cuenta_acumulativa_en_mov_en_el_que_era_interactiva_devuelve_saldo_historico_distinto_de_cero(
        cuenta, entrada):
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1 saldo 0', 'sc1', 0],
        ['subcuenta 2 saldo 0', 'sc2'],
    )
    assert cuenta.saldo(movimiento=entrada) != 0


def test_saldo_de_cuenta_acumulativa_en_mov_en_el_que_era_interactiva_devuelve_saldo_historico_correcto(
        cuenta, entrada, salida_posterior):
    saldo_historico = cuenta.saldo(movimiento=entrada)
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1 saldo 0', 'sc1', 0],
        ['subcuenta 2 saldo 0', 'sc2'],
    )
    assert cuenta.saldo(movimiento=entrada) != cuenta.saldo(movimiento=salida_posterior)
    assert cuenta.saldo(movimiento=entrada) == saldo_historico

@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_si_recibe_moneda_devuelve_saldo_en_moneda_dada_redondeado_en_2_decimales(
        tipo, cuenta_acumulativa_saldo_0, peso, dolar, fecha):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    Movimiento.crear('saldo sc1', 100, sc1, fecha=fecha)
    Movimiento.crear('saldo sc2', 70, None, sc2, fecha=fecha)

    compra = tipo == "compra"

    assert cuenta_acumulativa_saldo_0.saldo(moneda=dolar, compra=compra) == \
        round(
            cuenta_acumulativa_saldo_0.saldo() * cuenta_acumulativa_saldo_0.moneda.cotizacion_en(
                dolar, compra=compra
            ), 2
        )
    assert \
        cuenta_acumulativa_saldo_0.saldo(moneda=peso, compra=compra) == \
        cuenta_acumulativa_saldo_0.saldo()

@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_si_recibe_moneda_y_movimiento_devuelve_saldo_en_movimiento_dado_en_moneda_dada_a_la_fecha_del_movimiento_redondeado_en_2_decimales(
        tipo, cuenta_acumulativa_saldo_0, peso, dolar, fecha, fecha_posterior, cotizacion_posterior):
    cuenta = cuenta_acumulativa_saldo_0
    sc1, sc2 = cuenta.subcuentas.all()
    mov = Movimiento.crear('saldo sc1', 100, sc1, fecha=fecha)
    Movimiento.crear('saldo sc2', 70, None, sc2, fecha=fecha_posterior)

    compra = tipo == "compra"
    assert \
        cuenta.saldo(mov, dolar, compra) == \
        round(
            cuenta.saldo(movimiento=mov) * cuenta.moneda.cotizacion_en_al(
                dolar, fecha=mov.fecha, compra=compra
            ),
            2
        )
    assert cuenta.saldo(mov, peso, compra) == cuenta.saldo(movimiento=mov)


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_saldo_de_cuenta_acumulativa_en_mov_en_el_que_era_interactiva_devuelve_saldo_historico_correcto_en_monedad_dada(
        tipo, cuenta, entrada, peso, dolar, salida_posterior):
    compra = tipo == "compra"

    saldo_historico = cuenta.saldo(movimiento=entrada)
    saldo_historico_cotizado = cuenta.saldo(movimiento=entrada, moneda=dolar, compra=compra)

    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1 saldo 0', 'sc1', 0],
        ['subcuenta 2 saldo 0', 'sc2'],
    )
    assert cuenta.saldo(movimiento=entrada, moneda=dolar, compra=compra) == saldo_historico_cotizado
    assert cuenta.saldo(movimiento=entrada, moneda=peso, compra=compra) == saldo_historico
