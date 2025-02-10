import pytest

from diario.models import Movimiento, Moneda, Cotizacion
from utils.varios import el_que_no_es


def test_guarda_y_recupera_movimientos(fecha, dia, cuenta, cuenta_2):
    cantidad_movimientos = Movimiento.cantidad()
    mov = Movimiento()
    mov.dia = dia
    mov.concepto = 'entrada de efectivo'
    mov.importe = 985.5
    mov.cta_entrada = cuenta
    mov.cta_salida = cuenta_2
    mov.detalle = "Detalle del movimiento"
    mov.moneda = cuenta.moneda
    mov.cotizacion = 1.0
    mov.save()

    assert Movimiento.cantidad() == cantidad_movimientos + 1

    mov_guardado = Movimiento.tomar(pk=mov.pk)

    assert mov_guardado.dia == dia
    assert mov_guardado.fecha == dia.fecha
    assert mov_guardado.concepto == 'entrada de efectivo'
    assert mov_guardado.importe == 985.5
    assert mov_guardado.cta_entrada == cuenta
    assert mov_guardado.cta_salida == cuenta_2
    assert mov_guardado.detalle == "Detalle del movimiento"
    assert mov_guardado.moneda == cuenta.moneda
    assert mov_guardado.cotizacion == 1.0


def test_cta_entrada_se_relaciona_con_cuenta(cuenta, fecha):
    mov = Movimiento(fecha=fecha, concepto='Cobranza en efectivo', importe=100)
    mov.cta_entrada = cuenta
    mov.full_clean()
    mov.save()
    assert mov in cuenta.entradas.all()


def test_cta_salida_se_relaciona_con_cuenta(cuenta, fecha):
    mov = Movimiento(fecha=fecha, concepto='Pago en efectivo', importe=100)
    mov.cta_salida = cuenta
    mov.full_clean()
    mov.save()
    assert mov in cuenta.salidas.all()


def test_se_relaciona_con_dia(cuenta, importe, dia):
    mov = Movimiento(concepto='Entrada', importe=importe, cta_entrada=cuenta)
    mov.dia = dia
    mov.full_clean()
    mov.save()
    assert mov in dia.movimiento_set.all()


def test_movimientos_se_ordenan_por_dia(entrada, entrada_tardia, entrada_anterior):
    assert list(Movimiento.todes()) == [entrada_anterior, entrada, entrada_tardia]


def test_dentro_del_dia_movimientos_se_ordenan_por_campo_orden_dia(cuenta, dia):
    mov1 = Movimiento.crear(
        dia=dia,
        concepto='Mov1',
        importe=100,
        cta_salida=cuenta,
    )
    mov2 = Movimiento.crear(
        dia=dia,
        concepto='Mov2',
        importe=100,
        cta_entrada=cuenta,
    )
    mov3 = Movimiento.crear(
        dia=dia,
        concepto='Mov3',
        importe=243,
        cta_entrada=cuenta,
    )

    mov3.orden_dia = 0
    mov3.full_clean()
    mov3.save()
    mov1.refresh_from_db()
    mov2.refresh_from_db()

    assert list(Movimiento.todes()) == [mov3, mov1, mov2]


def test_moneda_base_es_moneda_por_defecto(cuenta, fecha, mock_moneda_base):
    mov = Movimiento(fecha=fecha, concepto='Pago en efectivo', importe=100, cta_entrada=cuenta)
    mov.full_clean()
    mov.save()
    assert mov.moneda == Moneda.tomar(monname=mock_moneda_base)


def test_cotizacion_por_defecto_es_1_para_cuentas_con_la_misma_moneda(cuenta, cuenta_2, fecha):
    mov = Movimiento(
        fecha=fecha, concepto="Movimiento entre cuentas en la misma moneda", importe=100,
        cta_entrada=cuenta, cta_salida=cuenta_2
    )
    mov.full_clean()
    mov.save()
    assert mov.cotizacion == 1


@pytest.mark.parametrize("sentido", ["cta_entrada", "cta_salida"])
def test_en_movimientos_de_entrada_o_salida_cotizacion_es_siempre_uno(cuenta, fecha, sentido):
    kwargs = {
        'fecha': fecha,
        'concepto': 'Entrada o salida',
        'importe': 100,
        sentido: cuenta,
        'cotizacion': 50
    }
    mov = Movimiento(**kwargs)
    mov.full_clean()
    mov.save()
    assert mov.cotizacion == 1


def test_en_movimientos_entre_cuentas_en_la_misma_moneda_cotizacion_es_siempre_uno(cuenta, cuenta_2, fecha):
    mov = Movimiento(
        fecha=fecha, concepto="Movimiento entre cuentas en la misma moneda", importe=100,
        cta_entrada=cuenta, cta_salida=cuenta_2, cotizacion=55
    )
    mov.full_clean()
    mov.save()
    assert mov.cotizacion == 1


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_entre_cuentas_en_distinta_moneda_se_calcula_cotizacion_a_partir_de_la_cotizacion_de_ambas_monedas_a_la_fecha_del_movimiento(
        sentido, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros, dolar, euro,
        cotizacion, cotizacion_posterior, cotizacion_euro, cotizacion_posterior_euro, fecha):
    compra = sentido == "salida"
    sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")

    mov = Movimiento(
        fecha=fecha, concepto="Compra de dólares con euros", importe=100,
        moneda=euro
    )
    setattr(mov, f"cta_{sentido}", cuenta_con_saldo_en_dolares)
    setattr(mov, f"cta_{sentido_opuesto}", cuenta_con_saldo_en_euros)

    mov.full_clean()
    mov.save()

    assert mov.cotizacion == dolar.cotizacion_en_al(euro, fecha, compra=compra)


def test_entre_cuentas_en_distinta_moneda_permite_cotizacion_arbitraria(
        cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros, dolar, euro,
        cotizacion, cotizacion_posterior, cotizacion_euro, cotizacion_posterior_euro, fecha):
    mov = Movimiento(
        fecha=fecha, concepto="Compra de dólares con euros", importe=100,
        cta_entrada=cuenta_con_saldo_en_dolares, cta_salida=cuenta_con_saldo_en_euros,
        moneda=euro
    )
    mov.cotizacion = 555
    mov.full_clean()
    mov.save()
    assert mov.cotizacion == 555

def test_natural_key_devuelve_fecha_y_orden_dia(entrada):
    assert entrada.natural_key() == (entrada.dia.fecha, entrada.orden_dia, )
