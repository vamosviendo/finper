from __future__ import annotations
from datetime import date

from django.core.exceptions import ValidationError

from diario.models import CuentaInteractiva, CuentaAcumulativa, Movimiento


def cambiar_fecha(mov: Movimiento, fecha: date):
    mov.fecha = fecha
    mov.clean_save()


def cambiar_fecha_creacion(cuenta: CuentaInteractiva | CuentaAcumulativa, fecha: date):
    cuenta.fecha_creacion = fecha
    try:
        cuenta.clean_save()
    except ValidationError:
        cuenta.titular.fecha_alta = fecha
        cuenta.titular.clean_save()


def dividir_en_dos_subcuentas(cuenta: CuentaInteractiva, saldo: float = 0, fecha: date = None) -> CuentaAcumulativa:
    return cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', saldo],
        ['subcuenta 2', 'sc2'],
        fecha=fecha
    )


def signo(condicion: bool) -> int:
    return 1 if condicion else -1
