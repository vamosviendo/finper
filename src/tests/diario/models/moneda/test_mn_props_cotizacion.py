from datetime import date

import pytest

from diario.models import Cotizacion, Moneda


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_importe_de_la_cotizacion_de_fecha_mas_reciente(
        tipo, dolar, cotizacion_posterior_dolar, cotizacion_tardia_dolar):
    cotizacion = getattr(dolar, f"cotizacion_{tipo}")
    importe = getattr(cotizacion_tardia_dolar, f"importe_{tipo}")
    assert cotizacion == importe


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_1_si_no_hay_cotizaciones(tipo, dolar):
    for cot in dolar.cotizaciones.all():
        cot.delete()
    assert dolar.cotizaciones.count() == 0
    cotizacion = getattr(dolar, f"cotizacion_{tipo}")
    assert cotizacion == 1


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_importe_de_la_cotizacion_cargada_si_es_distinta_de_la_existente_de_fecha_mas_reciente(tipo, dolar):
    cot = Cotizacion(moneda=dolar, fecha=date.today())
    setattr(cot, f"importe_{tipo}", 7.5)
    cot.clean_save()
    assert getattr(dolar, f"cotizacion_{tipo}") == 7.5


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_1_si_la_moneda_no_esta_en_la_base_de_datos_y_no_hay_cotizacion_cargada(tipo):
    moneda = Moneda(nombre="Moneda", sk="m")
    assert getattr(moneda, f"cotizacion_{tipo}") == 1


def test_prop_cotizacion_devuelve_cotizacion_venta(dolar, mocker):
    mocker.patch(
        "diario.models.Moneda.cotizacion_venta",
        return_value = 2.5,
        new_callable=mocker.PropertyMock,
    )
    assert dolar.cotizacion == 2.5
