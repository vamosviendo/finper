from diario.models import CuentaInteractiva, CuentaAcumulativa


def dividir_en_dos_subcuentas(cuenta: CuentaInteractiva, saldo=0, fecha=None) -> CuentaAcumulativa:
    return cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', saldo],
        ['subcuenta 2', 'sc2'],
        fecha=fecha
    )


def signo(condicion: bool) -> int:
    return 1 if condicion else -1
