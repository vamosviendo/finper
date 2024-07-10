def test_devuelve_importe_de_la_cotizacion_de_fecha_mas_reciente(
        dolar, cotizacion_posterior, cotizacion_tardia):
    assert dolar.cotizacion == cotizacion_tardia.importe


def test_devuelve_1_si_no_hay_cotizaciones(peso):
    assert peso.cotizacion == 1


def test_setter_genera_atributo__cotizacion(dolar):
    assert not hasattr(dolar, "_cotizacion")
    dolar.cotizacion = 235
    assert hasattr(dolar, "_cotizacion")


def test_atributo__cotizacion_creado_por_setter_tiene_fecha_actual(dolar, mock_today):
    dolar.cotizacion = 5
    assert getattr(dolar, "_cotizacion").fecha == mock_today.return_value
