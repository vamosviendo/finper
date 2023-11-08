from diario.models.moneda import Moneda
from diario.settings_app import MONEDA_BASE
from utils import errors


def moneda_base() -> Moneda:
    try:
        print(MONEDA_BASE)
        return Moneda.tomar(monname=MONEDA_BASE)
    except Moneda.DoesNotExist:
        raise errors.ErrorMonedaBaseInexistente
