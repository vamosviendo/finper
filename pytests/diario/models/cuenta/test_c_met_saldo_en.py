import pytest

@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_saldo_en_moneda_dada_redondeado_en_2_decimales(tipo, cuenta_con_saldo, peso, dolar):
    compra = tipo == "compra"
    assert \
        cuenta_con_saldo.saldo_en(dolar, compra=compra) == \
        round(cuenta_con_saldo.saldo() * cuenta_con_saldo.moneda.cotizacion_en(dolar, compra=compra), 2)
    assert cuenta_con_saldo.saldo_en(peso, compra=compra) == cuenta_con_saldo.saldo()
