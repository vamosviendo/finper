import pytest

@pytest.mark.parametrize("fixture_mov", ["entrada", "salida"])
@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_saldo_en_movimiento_dado_en_moneda_dada_a_la_fecha_del_movimiento_redondeado_en_2_decimales(
        fixture_mov, tipo, cuenta, peso, dolar, cotizacion_posterior, request):
    mov = request.getfixturevalue(fixture_mov)
    compra = tipo == "compra"
    assert \
        cuenta.saldo(mov, dolar, compra=compra) == \
        round(cuenta.saldo(mov) * cuenta.moneda.cotizacion_en_al(dolar, fecha=mov.fecha, compra=compra), 2)
    assert cuenta.saldo(mov, peso, compra=compra) == cuenta.saldo(mov)
