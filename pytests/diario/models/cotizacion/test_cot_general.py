from diario.models import Cotizacion


def test_se_relaciona_con_una_moneda(dolar, fecha):
    cotizacion = Cotizacion.crear(
        moneda=dolar,
        fecha=fecha,
        importe=1420,
    )
    cotizacion_dolar = dolar.cotizaciones.get(fecha=fecha)
    assert cotizacion_dolar == cotizacion


def test_se_ordena_por_fecha(dolar, cotizacion_tardia, cotizacion, cotizacion_posterior):
    assert list(Cotizacion.todes()) == [cotizacion, cotizacion_posterior, cotizacion_tardia]
