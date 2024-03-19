from diario.models import Movimiento, Moneda


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
