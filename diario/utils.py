from typing import List

from diario.models import Cuenta, Moneda, Movimiento
from diario.settings_app import MONEDA_BASE
from utils import errors


def verificar_saldos() -> List[Cuenta]:
    ctas_erroneas = []
    for cuenta in Cuenta.todes():
        if not cuenta.saldo_ok():
            ctas_erroneas.append(cuenta)
    return ctas_erroneas


def saldo_general_historico(mov: Movimiento) -> float:
    return sum([
        cuenta.saldo_en_mov(mov) for cuenta in Cuenta.filtro(cta_madre=None)
    ])


def moneda_base() -> Moneda:
    try:
        return Moneda.tomar(monname=MONEDA_BASE)
    except Moneda.DoesNotExist:
        raise errors.ErrorMonedaBaseInexistente
