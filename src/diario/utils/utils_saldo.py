from __future__ import annotations

from typing import List, TYPE_CHECKING, Optional, Iterable

from diario.models import Cuenta, Moneda, SaldoDiario, Cotizacion, Movimiento, Dia
from utils.numeros import float_format

if TYPE_CHECKING:
    from diario.models import Dia


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
        cuentas: Optional[Iterable] = None) -> float:
    if not mov and not dia:
        dia = Dia.ultime()
        if not dia:
            return 0

    fecha = mov.fecha if mov else dia.fecha
    cuentas_a_sumar = list(cuentas or Cuenta.filtro(cta_madre=None))
    cotizacion = moneda.cotizacion_al(fecha=fecha, compra=compra) if moneda else 1

    if not cuentas_a_sumar:
        return 0
    if mov:
        saldos = SaldoDiario.saldos_cuentas(cuentas_a_sumar, movimiento=mov)
    else:
        saldos = SaldoDiario.saldos_cuentas(cuentas_a_sumar, dia=dia)
    saldo_general = sum(saldos.get(c.pk, 0.0) for c in cuentas_a_sumar)

    return round(saldo_general / cotizacion, 2)


def precalcular_saldos_cuentas(
        cuentas: Iterable[Cuenta],
        monedas: Iterable[Moneda],
        dia: Dia | None = None,
        movimiento: Movimiento | None = None):

    if not dia and not movimiento:
        raise ValueError(
            "Debe proporcionarse un día o un movimiento "
            "para el cálculo de los saldos"
        )

    cotizaciones = Cotizacion.indexar(
        cuentas,
        monedas,
        dia.fecha if dia else movimiento.dia.fecha
    )

    if movimiento:
        saldos = SaldoDiario.saldos_cuentas(cuentas, movimiento=movimiento)
    else:
        saldos = SaldoDiario.saldos_cuentas(cuentas, dia=dia)

    return {
        cuenta.pk: {
            moneda.sk: float_format(
                saldos.get(cuenta.pk, 0) *
                cotizaciones.get((cuenta.moneda_id, moneda.pk), 1.0),
            ) for moneda in monedas
        } for cuenta in cuentas
    }
