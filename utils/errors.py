from django.core.exceptions import ValidationError

CAMPO_VACIO = 'Este campo es obligatorio.'
CUENTA_INEXISTENTE = 'Debe haber una cuenta de entrada, una de salida o ambas.'
CUENTA_NO_INTERACTIVA = \
    'Se intentó usar una cuenta no interactiva en un movimiento.'
CUENTAS_IGUALES = 'Cuentas de entrada y salida no pueden ser la misma.'
ERROR_OPCIONES = 'Error no especificado en el campo opciones de Cuenta.'
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


class ErrorOpciones(ValueError):
    """ Error en el campo switches de Cuenta."""

    def __init__(self, message=ERROR_OPCIONES):
        super().__init__(message)


class ErrorDeSuma(ValidationError):

    def __init__(self, message='Suma no coincide'):
        super().__init__(message)
