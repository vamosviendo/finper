import pytest

from utils.varios import el_que_no_es


@pytest.mark.parametrize("fixt_moneda, fixt_otra_moneda", [("dolar", "euro"), ("euro", "dolar")])
@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_cotizacion_de_una_moneda_en_otra_moneda_dada_a_la_fecha_dada(
        tipo, fixt_moneda, fixt_otra_moneda, request,
        cotizacion_posterior, cotizacion_tardia,
        cotizacion_posterior_euro, cotizacion_tardia_euro, fecha_posterior):
    compra = tipo == "compra"
    moneda = request.getfixturevalue(fixt_moneda)
    otra_moneda = request.getfixturevalue(fixt_otra_moneda)
    tipo_opuesto = el_que_no_es(tipo, "compra", "venta")
    assert \
        moneda.cotizacion_en_al(otra_moneda, fecha_posterior, compra=compra) == \
        moneda.cotizacion_al(
            fecha_posterior, compra=compra
        ) / otra_moneda.cotizacion_al(
            fecha_posterior, compra=not compra
        )


@pytest.mark.parametrize("compra", [True, False])
def test_devuelve_1_si_ambas_monedas_son_la_misma(
        compra, dolar, cotizacion_posterior, cotizacion_tardia, fecha_posterior):
    assert dolar.cotizacion_en_al(dolar, fecha_posterior, compra=compra) == 1


@pytest.mark.parametrize("fixt_moneda", ["dolar", "euro"])
@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_compra_venta_ejecuta_cotizacion_en_al_con_el_valor_correspondiente_de_compra(
        tipo, fixt_moneda, request,
        cotizacion_posterior, cotizacion_tardia,
        cotizacion_posterior_euro, cotizacion_tardia_euro, fecha_posterior, mocker):
    moneda = request.getfixturevalue(fixt_moneda)
    otra_moneda = request.getfixturevalue(el_que_no_es(fixt_moneda, "dolar", "euro"))
    compra = tipo == "compra"
    mock_cotizacion_en_al = mocker.patch("diario.models.Moneda.cotizacion_en_al")

    cotizacion_moneda_en_al = getattr(moneda, f"cotizacion_{tipo}_en_al")

    cotizacion_moneda_en_al(otra_moneda, fecha_posterior)

    mock_cotizacion_en_al.assert_called_once_with(otra_moneda, fecha_posterior, compra=compra)
