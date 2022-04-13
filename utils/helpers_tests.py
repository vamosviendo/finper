def dividir_en_dos_subcuentas(cuenta, saldo=0, fecha=None):
    return cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', saldo],
        ['subcuenta 2', 'sc2'],
        fecha=fecha
    )
