from diario.models import Movimiento


def test_guarda_y_recupera_movimientos(fecha, cuenta, cuenta_2):
    cantidad_movimientos = Movimiento.cantidad()
    mov = Movimiento()
    mov.fecha = fecha
    mov.concepto = 'entrada de efectivo'
    mov.importe = 985.5
    mov.cta_entrada = cuenta
    mov.cta_salida = cuenta_2
    mov.detalle = "Detalle del movimiento"
    mov.save()

    assert Movimiento.cantidad() == cantidad_movimientos + 1

    mov_guardado = Movimiento.tomar(pk=mov.pk)

    assert mov_guardado.fecha == fecha
    assert mov_guardado.concepto == 'entrada de efectivo'
    assert mov_guardado.importe == 985.5
    assert mov_guardado.cta_entrada == cuenta
    assert mov_guardado.cta_salida == cuenta_2
    assert mov_guardado.detalle == "Detalle del movimiento"


def test_cta_entrada_se_relaciona_con_cuenta(cuenta, fecha):
    mov = Movimiento(fecha=fecha, concepto='Cobranza en efectivo', importe=100)
    mov.cta_entrada = cuenta
    mov.save()
    assert mov in cuenta.entradas.all()

def test_cta_salida_se_relaciona_con_cuenta(cuenta, fecha):
    mov = Movimiento(fecha=fecha, concepto='Pago en efectivo', importe=100)
    mov.cta_salida = cuenta
    mov.save()
    assert mov in cuenta.salidas.all()


def test_movimientos_se_ordenan_por_fecha(entrada, entrada_tardia, entrada_anterior):
    assert list(Movimiento.todes()) == [entrada_anterior, entrada, entrada_tardia]


def test_dentro_de_fecha_movimientos_se_ordenan_por_campo_orden_dia(cuenta, fecha):
    mov1 = Movimiento.crear(
        fecha=fecha,
        concepto='Mov1',
        importe=100,
        cta_salida=cuenta,
    )
    mov2 = Movimiento.crear(
        fecha=fecha,
        concepto='Mov2',
        importe=100,
        cta_entrada=cuenta,
    )
    mov3 = Movimiento.crear(
        fecha=fecha,
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
