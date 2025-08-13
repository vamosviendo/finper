from __future__ import annotations

from typing import List, TYPE_CHECKING, Optional

from diario.models import Cuenta, Moneda

if TYPE_CHECKING:
    from diario.models import Movimiento, Dia


def verificar_saldos() -> List['Cuenta']:
    ctas_erroneas = []
    for cuenta in Cuenta.todes():
        if not cuenta.saldo_ok():
            ctas_erroneas.append(cuenta)
    return ctas_erroneas


def saldo_general_historico(
        mov: Optional['Movimiento'] = None,
        dia: Optional[Dia] = None,
        moneda: Optional[Moneda] = None, compra: bool = False) -> float:
    if not mov and not dia:
        raise ValueError("Debe pasarse un movimiento o un día")
    fecha = mov.fecha if mov else dia.fecha
    cotizacion = moneda.cotizacion_al(fecha=fecha, compra=compra) if moneda else 1
    if dia:
        saldo_general = sum(cuenta.saldo(dia=dia) for cuenta in Cuenta.filtro(cta_madre=None))
    else:
        saldo_general = sum(cuenta.saldo(movimiento=mov) for cuenta in Cuenta.filtro(cta_madre=None))
    return round(saldo_general / cotizacion, 2)
