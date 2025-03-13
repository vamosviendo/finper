from typing import List, TYPE_CHECKING

from diario.models import Cuenta


if TYPE_CHECKING:
    from diario.models import Movimiento


def verificar_saldos() -> List['Cuenta']:
    ctas_erroneas = []
    for cuenta in Cuenta.todes():
        if not cuenta.saldo_ok():
            ctas_erroneas.append(cuenta)
    return ctas_erroneas


def saldo_general_historico(mov: 'Movimiento') -> float:
    return sum([
        cuenta.saldo(mov) for cuenta in Cuenta.filtro(cta_madre=None)
    ])
