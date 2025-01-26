import pytest

from diario.models import Cotizacion
from utils.varios import el_que_no_es


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
def test_setters_generan_atributo__cotizacion_si_no_existe(sentido, dolar):
    assert not hasattr(dolar, f"_cotizacion")
    setattr(dolar, f"cotizacion_{sentido}", 235)
    assert hasattr(dolar, f"_cotizacion")


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_atributo__cotizacion_creado_por_setters_es_de_clase_Cotizacion(sentido, dolar):
    setattr(dolar, f"cotizacion_{sentido}", 236)
    assert isinstance(dolar._cotizacion, Cotizacion)


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_atributo__cotizacion_creado_por_setters_tiene_fecha_actual(sentido, dolar, mock_today):
    setattr(dolar, f"cotizacion_{sentido}", 5)
    assert dolar._cotizacion.fecha == mock_today.return_value


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_setter_guarda_importe_correspondiente_en_atributo__cotizacion(sentido, dolar):
    setattr(dolar, f"cotizacion_{sentido}", 5)
    assert getattr(dolar._cotizacion, f"importe_{sentido}") == 5


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_setter_guarda_importe_correspondiente_en_atributo__cotizacion_existente(sentido, dolar):
    contrasentido = el_que_no_es(sentido, "compra", "venta")
    setattr(dolar, f"cotizacion_{contrasentido}", 7)
    setattr(dolar, f"cotizacion_{sentido}", 10)
    assert getattr(dolar._cotizacion, f"importe_{sentido}") == 10
    assert getattr(dolar._cotizacion, f"importe_{contrasentido}") == 7


def test_prop_cotizacion_devuelve_cotizacion_venta(dolar, mocker):
    mocker.patch(
        "diario.models.Moneda.cotizacion_venta",
        return_value = 2.5,
        new_callable=mocker.PropertyMock,
    )
    assert dolar.cotizacion == 2.5
