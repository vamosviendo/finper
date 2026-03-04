from __future__ import annotations

from typing import List, TYPE_CHECKING, Optional

from diario.models import Cuenta, Moneda
from utils.numeros import float_format

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
        moneda: Optional[Moneda] = None,
        compra: bool = False,
        cuentas: Optional[list] = None) -> float:
    if not mov and not dia:
        raise ValueError("Debe pasarse un movimiento o un día")
    fecha = mov.fecha if mov else dia.fecha
    cotizacion = moneda.cotizacion_al(fecha=fecha, compra=compra) if moneda else 1

    cuentas_a_sumar = cuentas or Cuenta.filtro(cta_madre=None)
    if dia:
        saldo_general = sum(cuenta.saldo(dia=dia) for cuenta in cuentas_a_sumar)
    else:
        saldo_general = sum(cuenta.saldo(movimiento=mov) for cuenta in cuentas_a_sumar)

    return round(saldo_general / cotizacion, 2)


def precalcular_saldos_cuentas(
        cuentas: list[Cuenta],
        monedas: list[Moneda],
        dia: Dia | None = None,
        movimiento: Movimiento | None = None):

    if not dia and not movimiento:
        raise ValueError(
            "Debe proporcionarse un día o un movimiento "
            "para el cálculo de los saldos"
        )

    return {
        cuenta.pk: {
            moneda.sk: float_format(
                cuenta.saldo(
                    dia=dia,
                    movimiento=movimiento,
                    moneda=moneda, compra=True
                )
            )
            for moneda in monedas
        }
        for cuenta in cuentas
    }
