import datetime
import re

import pytest
from django.core.exceptions import ValidationError

from utils import errors
from vvmodel.errors import ErrorCambioEnCampoFijo


def test_cuenta_acumulativa_debe_tener_subcuentas(cuenta_acumulativa_saldo_0):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    sc1.delete()
    sc2.delete()
    with pytest.raises(
            ValidationError,
            match='Cuenta acumulativa debe tener subcuentas'):
        cuenta_acumulativa_saldo_0.full_clean()


def test_no_se_puede_asignar_cta_madre_a_cta_interactiva_existente(cuenta_2, cuenta_acumulativa):
    cuenta_2.cta_madre = cuenta_acumulativa

    with pytest.raises(
            ErrorCambioEnCampoFijo,
            match="No se puede cambiar valor del campo 'cta_madre'"
    ):
        cuenta_2.clean()


def test_no_se_puede_asignar_cta_madre_a_cta_acumulativa_existente(cuenta_acumulativa, cuenta_acumulativa_saldo_0):
    cuenta_acumulativa.cta_madre = cuenta_acumulativa_saldo_0

    with pytest.raises(
            ErrorCambioEnCampoFijo,
            match="No se puede cambiar valor del campo 'cta_madre'"
    ):
        cuenta_acumulativa.clean()


def test_no_puede_tener_fecha_de_conversion_posterior_a_la_fecha_de_creacion_de_sus_subcuentas(
        cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    sc1.fecha_creacion = sc2.fecha_creacion + datetime.timedelta(3)
    sc1.save()
    cuenta_acumulativa.fecha_conversion = sc2.fecha_creacion + datetime.timedelta(1)
    with pytest.raises(errors.ErrorFechaConversionPosteriorACreacionSubcuenta):
        cuenta_acumulativa.clean()


def test_no_puede_tener_fecha_de_creacion_posterior_a_la_fecha_de_conversion(cuenta_acumulativa):
    cuenta_acumulativa.fecha_creacion = cuenta_acumulativa.fecha_conversion + datetime.timedelta(1)
    with pytest.raises(errors.ErrorFechaCreacionPosteriorAConversion):
        cuenta_acumulativa.clean()


def test_no_puede_tener_fecha_de_creacion_anterior_a_fecha_de_alta_de_ninguno_de_sus_titulares(
        cuenta_de_dos_titulares):
    titular, otro_titular = cuenta_de_dos_titulares.titulares
    cuenta_de_dos_titulares.fecha_creacion = otro_titular.fecha_alta - datetime.timedelta(1)

    with pytest.raises(
            errors.ErrorFechaAnteriorAAltaTitular,
            match=f"[Fecha de creación de la cuenta {cuenta_de_dos_titulares.nombre} "
                f"({re.escape(str(cuenta_de_dos_titulares.fecha_creacion))}) posterior a la "
                f"fecha de alta de uno de sus titulares "
                f"({otro_titular} - {re.escape(str(otro_titular.fecha_alta))})]"
    ):
        cuenta_de_dos_titulares.clean()
