from datetime import date

from diario.models import Cuenta, CuentaInteractiva, CuentaAcumulativa, Movimiento


def cambiar_fecha(mov: Movimiento, fecha: date):
    mov.fecha = fecha
    mov.full_clean()
    mov.save()


def cambiar_fecha_creacion(cuenta: Cuenta, fecha: date):
    cuenta.fecha_creacion = fecha
    cuenta.full_clean()
    cuenta.save()


def dividir_en_dos_subcuentas(cuenta: CuentaInteractiva, saldo=0, fecha=None) -> CuentaAcumulativa:
    return cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', saldo],
        ['subcuenta 2', 'sc2'],
        fecha=fecha
    )


def signo(condicion: bool) -> int:
    return 1 if condicion else -1
