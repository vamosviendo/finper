from django.core.exceptions import ValidationError

CAMPO_VACIO = 'Este campo es obligatorio.'
CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA = \
    'Movimiento tiene cuenta acumulativa. No puede modificarse el importe'
CAMBIO_TITULAR = 'Las cuentas no pueden cambiar de titular.'
CUENTA_ACUMULATIVA_EN_MOVIMIENTO = \
    'No puede usarse cuenta acumulativa en movimiento'
CUENTA_ACUMULATIVA_AGREGADA = \
    'No puede agregarse cuenta acumulativa a movimiento'
CUENTA_ACUMULATIVA_RETIRADA = \
    'No puede retirarse cuenta acumulativa en movimiento'
MOVIMIENTO_CON_CA_ELIMINADO = \
    'Se intentó borrar un movimiento con una o más cuentas acumulativas'
CUENTA_INEXISTENTE = 'Debe haber una cuenta de entrada, una de salida o ambas'
CUENTAS_IGUALES = 'Cuentas de entrada y salida no pueden ser la misma'
FECHA_POSTERIOR_A_CONVERSION = 'Fecha del movimiento debe ser anterior a '
SALDO_NO_CERO = 'No se puede eliminar cuenta con saldo distinto de cero'
SALDO_NO_COINCIDE = 'El saldo de la cuenta no coincide con sus movimientos'
SUBCUENTAS_SIN_SALDO = 'Sólo se permite una subcuenta sin saldo'
SLUG_MAX_LENGTH = 'Longitud máxima de 4 caracteres para slug no automático'


class CambioDeTitularException(ValueError):
    """ Se intentó cambiar el titular de una cuenta"""
    def __init__(self, message=CAMBIO_TITULAR):
        super().__init__(message)


class SaldoNoCeroException(ValueError):
    """ Se eleva cuando se intenta eliminar una cuenta con saldo distinto de
        cero."""

    def __init__(self, message=SALDO_NO_CERO):
        super().__init__(message)


class SaldoNoCoincideException(ValueError):
    """ Saldo de cuenta no coincide con suma de sus movimientos."""

    def __init__(self, message=SALDO_NO_COINCIDE):
        super().__init__(message)


class ErrorDeSuma(ValidationError):

    def __init__(self, message='Suma no coincide'):
        super().__init__(message)


class ErrorTipo(ValidationError):

    def __init__(self, message='Incongruencia de tipo'):
        super().__init__(message)


class ErrorDependenciaCircular(ValidationError):

    def __init__(
            self,
            message='Intento de asignar dos cuentas mutuamente como subcuentas'
    ):
        super().__init__(message)


class ErrorCuentaEsInteractiva(TypeError):

    def __init__(
            self,
            message='Operación no admitida para cuentas interactivas'
    ):
        super().__init__(message)


class ErrorCuentaEsAcumulativa(TypeError):

    def __init__(
            self,
            message='Operación no admitida para cuentas acumulativas'
    ):
        super().__init__(message)


class ErrorImporteCero(ValueError):

    def __init__(
            self,
            message='No se admite importe igual a 0'
    ):
        super().__init__(message)


class ErrorMovimientoPosteriorAConversion(ValidationError):

    def __init__(
            self,
            message="Hay movimientos posteriores a la fecha de conversión "
                    "en cuenta acumulativa"
    ):
        super().__init__(message)


class ErrorOpcionInexistente(ValidationError):

    def __init__(
            self,
            message="Opción inexistente"
    ):
        super().__init__(message)


class ErrorMovimientoNoPrestamo(ValidationError):

    def __init__(
            self,
            message='Movimiento no es un préstamo'
    ):
        super().__init__(message)


class ErrorMovimientoAutomatico(ValidationError):

    def __init__(
            self,
            message='No se puede modificar o eliminar movimiento automático'
    ):
        super().__init__(message)