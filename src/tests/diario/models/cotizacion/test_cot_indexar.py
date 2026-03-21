from diario.models import Cotizacion


def test_devuelve_1_para_par_de_monedas_iguales(cuenta, peso, dia):
    resultado = Cotizacion.indexar([cuenta], [peso], dia.fecha)
    assert resultado[(cuenta.moneda_id, peso.pk)] == 1.0

def test_devuelve_factor_de_conversion_para_monedas_distintas(
        cuenta_con_saldo_en_dolares, peso, dolar, dia):
    resultado = Cotizacion.indexar(
        [cuenta_con_saldo_en_dolares], [peso], dia.fecha
    )
    cot = Cotizacion.tomar(moneda=dolar, fecha=dia.fecha)
    cot_peso = Cotizacion.tomar(moneda=peso, fecha=dia.fecha)
    esperado = cot.importe_venta / cot_peso.importe_compra
    assert resultado[(dolar.pk, peso.pk)] == esperado

def test_si_no_hay_cotizacion_devuelve_1(
        cuenta_con_saldo_en_dolares, peso, dolar, dia):
    dolar.cotizaciones.all().delete()
    resultado = Cotizacion.indexar(
        [cuenta_con_saldo_en_dolares], [peso], dia.fecha
    )
    assert resultado[(dolar.pk, peso.pk)] == 1.0

def test_no_repite_factor_para_misma_moneda_origen(
        cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_dolares_2,
        peso, dolar, dia):
    resultado = Cotizacion.indexar(
        [cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_dolares_2],
        [peso], dia.fecha
    )
    assert len([k for k in resultado if k[0] == dolar.pk]) == 1