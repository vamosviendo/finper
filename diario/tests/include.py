from datetime import date

from diario.models import Movimiento


def crear_entrada():
    return Movimiento.crear(
        fecha=date.today(),
        concepto='Movimiento de entrada',
        detalle='Detalle de entrada',
        entrada=250
    )

def crear_salida():
    return Movimiento.crear(
            fecha=date.today(),
            concepto='Movimiento de salida',
            detalle='Detalle de salida',
            salida=250
        )

def crear_traspaso():
    return Movimiento.crear(
            fecha=date.today(),
            concepto='Movimiento de traspaso',
            detalle='Detalle de traspaso',
            salida=300,
            entrada=300
        )