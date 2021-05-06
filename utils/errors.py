CAMPO_VACIO = 'Este campo es obligatorio.'
CUENTA_INEXISTENTE = 'Debe haber una cuenta de entrada, una de salida o ambas.'
CUENTAS_IGUALES = 'Cuentas de entrada y salida no pueden ser la misma.'
SALDO_NO_CERO = 'No se puede eliminar cuenta con saldo distinto de cero.'
SALDO_NO_COINCIDE = 'El saldo de la cuenta no coincide con sus movimientos.'


class SaldoNoCeroException(ValueError):
    """ Se eleva cuando se intenta eliminar una cuenta con saldo distinto de
        cero."""

    def __init__(self, message=SALDO_NO_CERO):
        super().__init__(message)


class SaldoNoCoincideException(ValueError):
    """ Saldo de cuenta no coincide con suma de sus movimientos."""

    def __init__(self, message=SALDO_NO_COINCIDE):
        super().__init__(message)