import datetime

import pytest
from django.core.exceptions import ValidationError

from diario.models import Movimiento
from utils import errors
from vvmodel.errors import ErrorCambioEnCampoFijo


def test_cuenta_acumulativa_debe_tener_subcuentas(cuenta_acumulativa_saldo_0):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    sc1.delete()
    sc2.delete()
    with pytest.raises(
            ValidationError,
            match='Cuenta acumulativa debe tener subcuentas'):
        cuenta_acumulativa_saldo_0.limpiar()


def test_no_se_puede_asignar_cta_madre_a_cta_interactiva_existente(cuenta_2, cuenta_acumulativa, fecha_posterior):
    cuenta_2.fecha_creacion = fecha_posterior
    cuenta_2.save()
    cuenta_2.cta_madre = cuenta_acumulativa

    with pytest.raises(
            ErrorCambioEnCampoFijo,
            match="No se puede cambiar valor del campo 'cta_madre'"
    ):
        cuenta_2.limpiar()


def test_no_se_puede_asignar_cta_madre_a_cta_acumulativa_existente(cuenta_acumulativa, cuenta_acumulativa_saldo_0):
    cuenta_acumulativa.cta_madre = cuenta_acumulativa_saldo_0

    with pytest.raises(
            ErrorCambioEnCampoFijo,
            match="No se puede cambiar valor del campo 'cta_madre'"
    ):
        cuenta_acumulativa.limpiar()


def test_no_puede_tener_fecha_de_creacion_posterior_a_la_fecha_de_conversion(cuenta_acumulativa):
    cuenta_acumulativa.fecha_creacion = cuenta_acumulativa.fecha_conversion + datetime.timedelta(1)
    with pytest.raises(errors.ErrorFechaCreacionPosteriorAConversion):
        cuenta_acumulativa.limpiar()


def test_no_puede_tener_fecha_de_conversion_posterior_a_la_fecha_de_creacion_de_sus_subcuentas(
        cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    sc1.fecha_creacion = sc2.fecha_creacion + datetime.timedelta(3)
    sc1.save()
    cuenta_acumulativa.fecha_conversion = sc2.fecha_creacion + datetime.timedelta(1)
    with pytest.raises(errors.ErrorFechaConversionPosteriorACreacionSubcuenta):
        cuenta_acumulativa.limpiar()


def test_no_puede_tener_fecha_de_conversion_anterior_a_la_de_su_ultimo_movimiento_como_cuenta_interactiva(
        cuenta_acumulativa):
    ultimo_mov_directo = cuenta_acumulativa.movs_directos().last()
    cuenta_acumulativa.fecha_conversion = ultimo_mov_directo.fecha - datetime.timedelta(1)
    with pytest.raises(ValidationError):
        cuenta_acumulativa.limpiar()


def test_no_puede_tener_fecha_de_conversion_posterior_a_la_del_primer_movimiento_de_cualquiera_de_sus_subcuentas(
        cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    mov = Movimiento.crear(
        fecha=cuenta_acumulativa.fecha_conversion + datetime.timedelta(1),
        concepto="Movimiento de subcuenta 1",
        importe=100,
        cta_entrada=sc1,
    )
    cuenta_acumulativa.fecha_conversion = mov.fecha + datetime.timedelta(1)
    with pytest.raises(ValidationError):
        cuenta_acumulativa.limpiar()

def test_puede_tener_fecha_de_conversion_igual_o_posterior_a_la_de_su_ultimo_movimiento_como_cuenta_interactiva(
        cuenta, fecha_temprana, fecha_anterior, fecha):
    Movimiento.crear(fecha=fecha_temprana, concepto="Entrada", importe=100, cta_entrada=cuenta)
    ultimo_mov_directo = Movimiento.crear(fecha=fecha_anterior, concepto="Entrada", importe=100, cta_salida=cuenta)
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1 saldo 0', 'sc1', 0],
        ['subcuenta 2 saldo 0', 'sc2'],
        fecha=fecha
    )
    cuenta.fecha_conversion = ultimo_mov_directo.fecha + datetime.timedelta(1)
    cuenta.limpiar()


def test_puede_tener_fecha_de_conversion_anterior_o_igual_a_la_del_primer_movimiento_de_cualquiera_de_sus_subcuentas(
        cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    mov = Movimiento.crear(
        fecha=cuenta_acumulativa.fecha_conversion + datetime.timedelta(1),
        concepto="Movimiento de subcuenta 1",
        importe=100,
        cta_entrada=sc1,
    )
    cuenta_acumulativa.fecha_conversion = mov.fecha - datetime.timedelta(1)
    cuenta_acumulativa.limpiar()


def test_si_no_tiene_movimientos_como_cuenta_interactiva_puede_tener_fecha_de_conversion(
        cuenta_acumulativa_saldo_0):
    cuenta_acumulativa_saldo_0.limpiar()


def test_si_sus_subcuentas_tienen_saldo_no_se_la_puede_desactivar_aunque_su_saldo_sea_cero(
        cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    Movimiento.crear("Puesta en cero de cuenta madre", sc1.saldo() + sc2.saldo(), cta_salida=sc1)
    cuenta_acumulativa.activa = False
    with pytest.raises(ValidationError):
        cuenta_acumulativa.limpiar()


def test_no_se_permite_activar_directamente_una_cuenta_acumulativa_inactiva(cuenta_acumulativa_saldo_0):
    cuenta_acumulativa_saldo_0.activa = False
    cuenta_acumulativa_saldo_0.clean_save()

    cuenta_acumulativa_saldo_0.activa = True
    with pytest.raises(
            ValidationError,
            match="No se puede activar directamente una cuenta acumulativa inactiva. "
                "Intente activar una o más de sus subcuentas"
    ):
        cuenta_acumulativa_saldo_0.limpiar()
