from __future__ import annotations

from typing import List, TYPE_CHECKING, Optional, Iterable

from diario.models import Cuenta, Moneda, SaldoDiario, Cotizacion, Movimiento
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
        cuentas: Iterable[Cuenta],
        monedas: Iterable[Moneda],
        dia: Dia | None = None,
        movimiento: Movimiento | None = None):

    if not dia and not movimiento:
        raise ValueError(
            "Debe proporcionarse un día o un movimiento "
            "para el cálculo de los saldos"
        )

    cotizaciones = _indexar_cotizaciones(
        cuentas,
        monedas,
        dia.fecha if dia else movimiento.dia.fecha
    )

    cuentas_acumulativas = [c for c in cuentas if c.es_acumulativa]
    cuentas_interactivas = [c for c in cuentas if c not in cuentas_acumulativas]

    if movimiento:
        saldos = SaldoDiario.indexar_en_movimiento(cuentas_interactivas, movimiento)
        for cuenta in cuentas_acumulativas:
            saldos[cuenta.pk] = cuenta.saldo(movimiento=movimiento)

        return {
            cuenta.pk: {
                moneda.sk: float_format(
                    round(
                        saldos.get(cuenta.pk, 0) *
                        cotizaciones.get((cuenta.moneda_id, moneda.pk), 1.0),
                        2
                    )
                )
                for moneda in monedas
            }
            for cuenta in cuentas
        }

    saldos_diarios = SaldoDiario.indexar_por_dia(cuentas, dia)
    return {
        cuenta.pk: {
            moneda.sk: float_format(
                round(
                    saldos_diarios.get(cuenta.pk, 0) *
                    cotizaciones.get((cuenta.moneda_id, moneda.pk)),
                    2
                )
            ) for moneda in monedas
        } for cuenta in cuentas
    }


def _indexar_cotizaciones(cuentas, monedas, fecha) -> dict[tuple[int, int], float]:
    ids_monedas_origen = {c.moneda_id for c in cuentas}
    monedas_todas_ids = list({*ids_monedas_origen, *[m.pk for m in monedas]})
    cots_raw = Cotizacion.filtro(
        moneda__in=monedas_todas_ids,
        fecha__lte=fecha,
    ).order_by('moneda_id', '-fecha')
    vistos = set()
    cots_por_moneda = {}
    for cot in cots_raw:
        if cot.moneda_id not in vistos:
            cots_por_moneda[cot.moneda_id] = cot
            vistos.add(cot.moneda_id)

    cotizaciones = {}
    for id_moneda_origen in ids_monedas_origen:
        for moneda_destino in monedas:
            if id_moneda_origen == moneda_destino.pk:
                cotizaciones[(id_moneda_origen, moneda_destino.pk)] = 1.0
            else:
                cot_orig = cots_por_moneda.get(id_moneda_origen)
                cot_dest = cots_por_moneda.get(moneda_destino.pk)
                if cot_orig and cot_dest:
                    cotizaciones[(id_moneda_origen, moneda_destino.pk)] = (
                            cot_orig.importe_venta / cot_dest.importe_compra
                    )
                else:
                    cotizaciones[(id_moneda_origen, moneda_destino.pk)] = 1.0

    return cotizaciones
