from __future__ import annotations

from typing import List, TYPE_CHECKING, Optional

from django.core.exceptions import EmptyResultSet

from diario.models import Cuenta, Moneda, SaldoDiario, Cotizacion

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
        cuentas: list,
        monedas: list,
        dia: 'Dia') -> dict:
    """ Devuelve {cuenta_pk: {moneda_sk: saldo_formateado}} para todas las
        combinaciones de cuentas x monedas haciendo el mínimo de queries
        posible
    """
    from utils.numeros import float_format

    # 1 query: todos los saldos diarios del día para todas las cuentas
    saldos_diarios = {
        sd.cuenta_id: sd.importe
        for sd in SaldoDiario.filtro(dia=dia)
    }

    # 1 query por moneda (ya están en memoria se se pasó lista precargada,
    # pero es necesario buscar Cotizacion): traemos todas las cotizaciones
    # del día de una sola vez.
    cotizaciones = {}     # {(moneda_id, moneda_destino_id): valor}
    for moneda_destino in monedas:
        for moneda_origen in {c.moneda for c in cuentas}:
            if moneda_origen == moneda_destino:
                cotizaciones[(moneda_origen.pk, moneda_destino.pk)] = 1.0
            else:
                try:
                    cot = Cotizacion.tomar(moneda=moneda_origen, fecha=dia.fecha)
                    cot_destino = Cotizacion.tomar(moneda=moneda_destino, fecha=dia.fecha)
                    cotizaciones[(moneda_origen.pk, moneda_destino.pk)] = (
                        cot.importe_venta / cot_destino.importe_compra
                    )
                except EmptyResultSet:
                    cotizaciones[(moneda_origen.pk, moneda_destino.pk)] = 1.0

    # Calcular saldos en memoria sin más queries
    resultado = {}
    for cuenta in cuentas:
        importe_base = saldos_diarios.get(cuenta.pk)
        if importe_base is None:
            # Buscar el último saldo diario anterior
            sd_anterior = SaldoDiario.anterior_a(cuenta=cuenta, dia=dia)
            importe_base = sd_anterior.importe if sd_anterior else 0.0

        resultado[cuenta.pk] = {}
        for moneda in monedas:
            cot = cotizaciones.get((cuenta.moneda.pk, moneda.pk), 1.0)
            resultado[cuenta.pk][moneda.sk] = float_format(
                round(importe_base * cot, 2)
            )

    return resultado