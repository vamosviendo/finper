from diario.models import Cotizacion


def test_se_relaciona_con_una_moneda(dolar, fecha):
    cotizacion = Cotizacion.crear(
        moneda=dolar,
        fecha=fecha,
        importe=1420,
    )
    cotizacion_dolar = dolar.cotizaciones.get(fecha=fecha)
    assert cotizacion_dolar == cotizacion
