from datetime import date

from diario.models import Movimiento


def crear_entrada():
    return Movimiento.crear(
        fecha=date.today(),
        concepto='Movimiento de entrada',
        detalle='Detalle de entrada',
        importe=250,
        cta_entrada='Efectivo'
    )


def crear_salida():
    return Movimiento.crear(
            fecha=date.today(),
            concepto='Movimiento de salida',
            detalle='Detalle de salida',
            importe=250,
            cta_salida='Efectivo'
        )


def crear_traspaso():
    return Movimiento.crear(
            fecha=date.today(),
            concepto='Movimiento de traspaso',
            detalle='Detalle de traspaso',
            importe=300,
            cta_salida='Salida',
            cta_entrada='Entrada'
        )