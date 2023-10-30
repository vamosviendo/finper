import pytest
from django.core.exceptions import ValidationError

from diario.models import CuentaInteractiva
from utils import errors


@pytest.fixture
def mock_titular_principal(titular, otro_titular, mocker):
    mock_titular_principal = mocker.patch(
        'diario.models.cuenta.TITULAR_PRINCIPAL',
        otro_titular.titname
    )
    return mock_titular_principal


def test_completa_campo_titular_con_titular_por_defecto(mock_titular_principal, otro_titular):
    cuenta = CuentaInteractiva(nombre='Efectivo', slug='e')
    cuenta.clean()
    assert cuenta.titular == otro_titular


def test_si_no_existe_el_titular_por_defecto_da_error_de_validacion(
        mock_titular_principal, otro_titular):
    otro_titular.delete()
    cuenta = CuentaInteractiva(nombre='Efectivo', slug='e')
    with pytest.raises(errors.ErrorTitularPorDefectoInexistente):
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
