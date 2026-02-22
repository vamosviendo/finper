import pytest

from utils.varios import el_que_no_es


@pytest.mark.parametrize("fixt_moneda, fixt_otra_moneda", [("dolar", "euro"), ("euro", "dolar")])
@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_cotizacion_de_una_moneda_para_la_compra_en_otra_moneda_para_la_venta_o_viceversa(
        fixt_moneda, fixt_otra_moneda, tipo, request):
    compra = tipo == "compra"
    moneda = request.getfixturevalue(fixt_moneda)
    otra_moneda = request.getfixturevalue(fixt_otra_moneda)
    tipo_opuesto = el_que_no_es(tipo, "compra", "venta")
    assert \
        moneda.cotizacion_en(otra_moneda, compra=compra) == \
        getattr(moneda, f"cotizacion_{tipo}") / getattr(otra_moneda, f"cotizacion_{tipo_opuesto}")


@pytest.mark.parametrize("compra", [True, False])
def test_devuelve_1_si_otra_moneda_es_la_misma_que_self(dolar, compra):
    assert dolar.cotizacion_en(dolar, compra=compra) == 1
