import pytest

from diario.models import CuentaInteractiva
from utils import errors


def test_completa_campo_titular_vacio_con_el_primer_titular_disponible(titular, otro_titular):
    cuenta = CuentaInteractiva(nombre='Efectivo', slug='e')
    cuenta.clean()
    assert cuenta.titular == titular


def test_si_no_hay_titulares_da_error_de_validacion():
    cuenta = CuentaInteractiva(nombre='Efectivo', slug='e')
    with pytest.raises(errors.ErrorNoHayTitulares):
        cuenta.clean()


def test_cuenta_no_puede_cambiar_de_titular(cuenta, titular, otro_titular):
    cuenta.titular = otro_titular

    with pytest.raises(errors.CambioDeTitularException):
        cuenta.clean()


def test_cuenta_no_puede_tener_fecha_de_creacion_anterior_a_la_fecha_de_alta_de_su_titular(
        titular, fecha_anterior):
    cuenta = CuentaInteractiva(
        nombre='cuenta',
        slug='c',
        titular=titular,
        fecha_creacion=fecha_anterior
    )
    with pytest.raises(errors.ErrorFechaAnteriorAAltaTitular):
        cuenta.clean()
