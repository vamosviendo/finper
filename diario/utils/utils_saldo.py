from __future__ import annotations

from typing import List, TYPE_CHECKING

from diario.models import Cuenta, Moneda

if TYPE_CHECKING:
    from diario.models import Movimiento


def verificar_saldos() -> List['Cuenta']:
    ctas_erroneas = []
    for cuenta in Cuenta.todes():
        if not cuenta.saldo_ok():
            ctas_erroneas.append(cuenta)
    return ctas_erroneas


def saldo_general_historico(mov: 'Movimiento', moneda: Moneda | None = None, compra: bool = False) -> float:
    cotizacion = moneda.cotizacion_al(fecha=mov.fecha, compra=compra) if moneda else 1
    return sum([
        cuenta.saldo(mov) for cuenta in Cuenta.filtro(cta_madre=None)
    ]) / cotizacion
