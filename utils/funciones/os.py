import os
from getpass import getpass


def env_or_input(env_var, msj=None, password=False):
    """ Busca una variable en el entorno. Si no la encuentra, la pide.
        password=True: oculta el texto tipeado.
    """
    if msj is None:
        msj = f'Ingrese valor para {env_var}: '
    try:
        result = os.environ[env_var]
    except KeyError:
        if password:
            result = getpass(msj)
        else:
            result = input(msj)

    return result
