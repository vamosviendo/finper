from diario.models import Cotizacion


def test_devuelve_valor_de_cotizacion_vigente_a_la_fecha_dada(cotizacion, cotizacion_posterior, dolar, fecha):
    for cot in Cotizacion.todes():
        print(cot.fecha, cot.importe)
    cot_actual = Cotizacion.tomar(moneda=dolar, fecha=fecha)
    assert dolar.cotizacion_al(fecha) == cot_actual.importe
