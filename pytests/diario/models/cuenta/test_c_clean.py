import datetime

import pytest
from django.core.exceptions import ValidationError

from diario.models import Cuenta
from utils import errors


def test_no_permite_nombres_ni_slugs_duplicados(titular_principal):
    Cuenta.crear(nombre='Efectivo', slug='E')
    cuenta2 = Cuenta(nombre='Efectivo', slug='EF')

    with pytest.raises(ValidationError):
        cuenta2.full_clean()

    cuenta3 = Cuenta(nombre='Otro nombre', slug='e')

    with pytest.raises(ValidationError):
        cuenta3.full_clean()


def test_no_permite_nombres_duplicados_con_distintas_mayusculas(cuenta):
    cuenta2 = Cuenta(nombre='CUENTA', slug='xx')
    with pytest.raises(ValidationError):
        cuenta2.full_clean()


def test_no_permite_slug_vacio():
    cuenta = Cuenta(nombre='Efectivo')
    with pytest.raises(ValidationError):
        cuenta.full_clean()


def test_subcuenta_no_puede_tener_fecha_de_creacion_anterior_a_la_fecha_de_conversion_de_su_cuenta_madre(
        cuenta_acumulativa):
    sc1, _ = cuenta_acumulativa.subcuentas.all()
    sc1.fecha_creacion = cuenta_acumulativa.fecha_conversion - datetime.timedelta(days=1)
    with pytest.raises(errors.ErrorFechaAnteriorACuentaMadre):
        sc1.clean()


def test_cuenta_no_puede_cambiar_de_moneda(cuenta, dolar):
    cuenta.moneda = dolar
    with pytest.raises(errors.CambioDeMonedaException):
        cuenta.clean()
