import pytest

from diario.models import Movimiento
from utils.varios import el_que_no_es

@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_cuenta_cambia_por_cuenta_en_tercera_moneda_devuelve_true(
        sentido, cuenta_con_saldo_en_reales, request):
    movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    mon_mov = movimiento.moneda == getattr(movimiento, f"cta_{sentido}").moneda
    setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is True

@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_cuenta_cambia_por_cuenta_en_moneda_de_la_otra_cuenta_devuelve_true(
        sentido, request):
    movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    mon_mov = movimiento.moneda == getattr(movimiento, f"cta_{sentido}").moneda
    sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
    cuenta_nueva = getattr(movimiento, f"cta_{sentido_otra_cuenta}")

    # cuenta_nueva = request.getfixturevalue(fixture_cuenta)
    setattr(movimiento, f"cta_{sentido}", cuenta_nueva)
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is True

@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_cuenta_no_cambia_devuelve_false(sentido, request):
    movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    mon_mov = movimiento.moneda == getattr(movimiento, f"cta_{sentido}").moneda
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is False

@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_cuenta_cambia_por_cuenta_en_la_misma_moneda_devuelve_false(
        sentido, euro, request):
    movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    cuenta_a_reemplazar = getattr(movimiento, f"cta_{sentido}")
    mon_mov = movimiento.moneda == cuenta_a_reemplazar.moneda
    cuenta_nueva = request.getfixturevalue(
        "cuenta_en_euros" if cuenta_a_reemplazar.moneda == euro else "cuenta_en_dolares"
    )
    setattr(movimiento, f"cta_{sentido}", cuenta_nueva)
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is False

@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_cuenta_opuesta_cambia_y_cuenta_no_devuelve_false(
        sentido, cuenta_con_saldo_en_reales, request):
    movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    mon_mov = movimiento.moneda == getattr(movimiento, f"cta_{sentido}").moneda
    sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

    setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is False


def test_si_movimiento_es_nuevo_devuelve_true(cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros, euro):
    movimiento = Movimiento(
        concepto="Compra de euros con dólares",
        cta_entrada=cuenta_con_saldo_en_euros,
        cta_salida=cuenta_con_saldo_en_dolares,
        importe=200,
        moneda=euro,
    )
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=True) is True
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) is True
