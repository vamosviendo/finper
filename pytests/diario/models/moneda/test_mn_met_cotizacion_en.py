import pytest

from utils.varios import el_que_no_es


@pytest.mark.parametrize("fixt_moneda, fixt_otra_moneda", [("dolar", "euro"), ("euro", "dolar")])
@pytest.mark.parametrize("sentido, compra", [("compra", True), ("venta", False)])
def test_devuelve_cotizacion_de_una_moneda_para_la_compra_en_otra_moneda_para_la_venta_o_viceversa(
        fixt_moneda, fixt_otra_moneda, sentido, compra, request):
    moneda = request.getfixturevalue(fixt_moneda)
    otra_moneda = request.getfixturevalue(fixt_otra_moneda)
    sentido_otra_moneda = el_que_no_es(sentido, "compra", "venta")
    assert \
        moneda.cotizacion_en(otra_moneda, compra=compra) == \
        getattr(moneda, f"cotizacion_{sentido}") / getattr(otra_moneda, f"cotizacion_{sentido_otra_moneda}")
