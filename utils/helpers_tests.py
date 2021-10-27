import time

from selenium.common.exceptions import WebDriverException

def esperar(condicion, tiempo=2):
    """ Devuelve una función que espera un tiempo
        que se cumpla una condición.
        Requiere: time
                  selenium.common.exceptions.WebDriverException
    """

    def condicion_modificada(*args, **kwargs):
        arranque = time.time()
        while True:
            try:
                return condicion(*args, **kwargs)
            except (AssertionError, WebDriverException) as noesperomas:
                if time.time() - arranque > tiempo:
                    raise noesperomas
                time.sleep(0.2)

    return condicion_modificada


def dividir_en_dos_subcuentas(cuenta, saldo=0):
    return cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', saldo], ['subcuenta 2', 'sc2']
    )
