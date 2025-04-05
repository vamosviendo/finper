import pytest

from diario.models import Cotizacion, Moneda
from utils.varios import el_que_no_es


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_importe_de_la_cotizacion_de_fecha_mas_reciente(
        tipo, dolar, cotizacion_posterior, cotizacion_tardia):
    cotizacion = getattr(dolar, f"cotizacion_{tipo}")
    importe = getattr(cotizacion_tardia, f"importe_{tipo}")
    assert cotizacion == importe


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_1_si_no_hay_cotizaciones(tipo, dolar):
    for cot in dolar.cotizaciones.all():
        cot.delete()
    assert dolar.cotizaciones.count() == 0
    cotizacion = getattr(dolar, f"cotizacion_{tipo}")
    assert cotizacion == 1


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_setters_generan_atributo__cotizacion_si_no_existe(tipo, dolar):
    assert not hasattr(dolar, f"_cotizacion")
    setattr(dolar, f"cotizacion_{tipo}", 235)
    assert hasattr(dolar, f"_cotizacion")


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_atributo__cotizacion_creado_por_setters_es_de_clase_Cotizacion(tipo, dolar):
    setattr(dolar, f"cotizacion_{tipo}", 236)
    assert isinstance(dolar._cotizacion, Cotizacion)


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_atributo__cotizacion_creado_por_setters_tiene_fecha_actual(tipo, dolar, mock_today):
    setattr(dolar, f"cotizacion_{tipo}", 5)
    assert dolar._cotizacion.fecha == mock_today.return_value


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_setter_guarda_importe_correspondiente_en_atributo__cotizacion(tipo, dolar):
    setattr(dolar, f"cotizacion_{tipo}", 5)
    assert getattr(dolar._cotizacion, f"importe_{tipo}") == 5


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_setter_guarda_importe_correspondiente_en_atributo__cotizacion_existente(tipo, dolar):
    contratipo = el_que_no_es(tipo, "compra", "venta")
    setattr(dolar, f"cotizacion_{contratipo}", 7)
    setattr(dolar, f"cotizacion_{tipo}", 10)
    assert getattr(dolar._cotizacion, f"importe_{tipo}") == 10
    assert getattr(dolar._cotizacion, f"importe_{contratipo}") == 7


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_importe_de_la_cotizacion_cargada_si_es_distinta_de_la_existente_de_fecha_mas_reciente(tipo, dolar):
    setattr(dolar, f"cotizacion_{tipo}", 7.5)
    assert getattr(dolar, f"cotizacion_{tipo}") == 7.5


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_devuelve_importe_de_la_cotizacion_cargada_si_la_moneda_no_esta_en_la_base_de_datos(tipo):
    moneda = Moneda(nombre="Moneda", sk="m")
    setattr(moneda, f"cotizacion_{tipo}", 7.5)
    assert getattr(moneda, f"cotizacion_{tipo}") == 7.5


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


def test_prop_cotizacion_de_moneda_no_guardada(dolar):
    moneda = Moneda(nombre="Moneda", sk="m")
    moneda.cotizacion_compra = 5
    assert moneda.cotizacion_compra == 5

    dolar.cotizacion_compra = 89
    assert dolar.cotizacion_compra == 89

    moneda2 = Moneda(nombre="Moneda2", sk="m2")
    assert moneda2.cotizacion_compra == 1
