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

    if movimiento:
        saldos = _indexar_saldos_en_movimiento(cuentas, movimiento)

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

    saldos_diarios = _indexar_saldos_diarios(cuentas, dia)
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


def _indexar_saldos_diarios(
        cuentas: Iterable[Cuenta],
        dia: Dia) -> dict[int, float]:
    saldos_diarios = {
        sd.cuenta_id: sd.importe
        for sd in SaldoDiario.filtro(dia=dia)
    }

    cuentas_sin_sd = [c for c in cuentas if c.pk not in saldos_diarios]
    if cuentas_sin_sd:
        sds_anteriores = SaldoDiario.filtro(
            cuenta__in=cuentas_sin_sd,
            dia__fecha__lt=dia.fecha,
        ).order_by('cuenta_id', '-dia__fecha')
        vistos = set()
        for sd in sds_anteriores:
            if sd.cuenta_id not in vistos:
                saldos_diarios[sd.cuenta_id] = sd.importe
                vistos.add(sd.cuenta_id)

    return saldos_diarios


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

def _indexar_saldos_en_movimiento(
        cuentas: Iterable[Cuenta],
        movimiento: Movimiento) -> dict[int, float]:
    saldos_diarios = _indexar_saldos_diarios(cuentas, movimiento.dia)

    movs_posteriores = list(Movimiento.filtro(
        dia=movimiento.dia,
        orden_dia__gt=movimiento.orden_dia,
    ).select_related('cta_entrada', 'cta_salida'))

    ids_cuentas = {c.pk for c in cuentas}
    ajustes = {c.pk: 0.0 for c in cuentas}
    for mov in movs_posteriores:
        if mov.cta_entrada_id in ids_cuentas:
            ajustes[mov.cta_entrada_id] -= mov.importe_cta_entrada
        if mov.cta_salida_id in ids_cuentas:
            ajustes[mov.cta_salida_id] -= mov.importe_cta_salida

    return {
        cuenta_id: importe + ajustes[cuenta_id]
        for cuenta_id, importe in {
            c.pk: saldos_diarios.get(c.pk, 0.0) for c in cuentas
        }.items()
    }
