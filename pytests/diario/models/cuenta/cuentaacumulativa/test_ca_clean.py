import datetime

import pytest
from django.core.exceptions import ValidationError


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

    with pytest.raises(ValidationError):
        cuenta_2.full_clean()


def test_no_se_puede_asignar_cta_madre_a_cta_acumulativa_existente(cuenta_acumulativa, cuenta_acumulativa_saldo_0):
    cuenta_acumulativa.cta_madre = cuenta_acumulativa_saldo_0

    with pytest.raises(ValidationError):
        cuenta_acumulativa.full_clean()


def test_no_puede_tener_fecha_de_conversion_posterior_a_la_fecha_de_creacion_de_sus_subcuentas(
        cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    sc1.fecha_creacion = sc2.fecha_creacion + datetime.timedelta(3)
    sc1.save()
    cuenta_acumulativa.fecha_conversion = sc2.fecha_creacion + datetime.timedelta(1)
    with pytest.raises(ValidationError):
        cuenta_acumulativa.full_clean()


def test_no_puede_tener_fecha_de_creacion_posterior_a_la_fecha_de_conversion(cuenta_acumulativa):
    cuenta_acumulativa.fecha_creacion = cuenta_acumulativa.fecha_conversion + datetime.timedelta(1)
    with pytest.raises(ValidationError):
        cuenta_acumulativa.full_clean()


def test_no_puede_tener_fecha_de_creacion_anterior_a_fecha_de_alta_de_ninguno_de_sus_titulares(
        cuenta_de_dos_titulares, fecha_anterior):
    titular, otro_titular = cuenta_de_dos_titulares.titulares
    titular.fecha_creacion = fecha_anterior
    titular.save()
    cuenta_de_dos_titulares.fecha_creacion = otro_titular.fecha_alta - datetime.timedelta(1)
    with pytest.raises(ValidationError):
        cuenta_de_dos_titulares.full_clean()
