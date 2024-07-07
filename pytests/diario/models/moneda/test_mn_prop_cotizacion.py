from datetime import date

import pytest

from diario.models import Cotizacion


@pytest.fixture
def mock_date(mocker):
    mock = mocker.patch("diario.models.moneda.date")
    mock.today.return_value = date(2020, 5, 2)
    return mock


def test_devuelve_importe_de_la_cotizacion_de_fecha_mas_reciente(
        dolar, cotizacion_posterior, cotizacion_tardia):
    assert dolar.cotizacion == cotizacion_tardia.importe


def test_devuelve_1_si_no_hay_cotizaciones(peso):
    assert peso.cotizacion == 1


def test_setter_crea_cotizacion(dolar, mock_date):
    dolar.cotizacion = 235
    cotizacion = Cotizacion.tomar(moneda=dolar, fecha=date(2020, 5, 2))
    assert cotizacion.importe == 235


def test_cotizacion_creada_por_setter_tiene_fecha_actual(dolar, mock_date):
    dolar.cotizacion = 5
    cotizacion = Cotizacion.filtro(moneda=dolar).last()
    assert cotizacion.fecha == date(2020, 5, 2)


def test_si_ya_existe_cotizacion_con_fecha_actual_setter_actualiza_el_importe(dolar, mock_date):
    cot = Cotizacion.crear(moneda=dolar, fecha=mock_date.today(), importe=10)
    dolar.cotizacion = 5
    cotizacion = Cotizacion.tomar(id=cot.id)
    assert cotizacion.importe == 5
