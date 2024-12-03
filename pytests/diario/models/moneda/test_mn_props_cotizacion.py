import pytest

@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_devuelve_importe_de_la_cotizacion_de_fecha_mas_reciente(
        sentido, dolar, cotizacion_posterior, cotizacion_tardia):
    cotizacion = getattr(dolar, f"cotizacion_{sentido}")
    importe = getattr(cotizacion_tardia, f"importe_{sentido}")
    assert cotizacion == importe


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_devuelve_1_si_no_hay_cotizaciones(sentido, peso):
    cotizacion = getattr(peso, f"cotizacion_{sentido}")
    assert cotizacion == 1


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_setters_generan_atributos__cotizacion(sentido, dolar):
    assert not hasattr(dolar, f"_cotizacion_{sentido}")
    setattr(dolar, f"cotizacion_{sentido}", 235)
    assert hasattr(dolar, f"_cotizacion_{sentido}")


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_atributos__cotizacion_creados_por_setters_tienen_fecha_actual(sentido, dolar, mock_today):
    setattr(dolar, f"cotizacion_{sentido}", 5)
    assert getattr(dolar, f"_cotizacion_{sentido}").fecha == mock_today.return_value


def test_prop_cotizacion_devuelve_cotizacion_venta(dolar, mocker):
    mocker.patch(
        "diario.models.Moneda.cotizacion_venta",
        return_value = 2.5,
        new_callable=mocker.PropertyMock,
    )
    assert dolar.cotizacion == 2.5
