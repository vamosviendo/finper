import datetime
import re

import pytest

from diario.models import CuentaInteractiva
from utils import errors
from vvmodel.errors import ErrorCambioEnCampoFijo


# Fixtures

@pytest.fixture
def mock_titular_principal(titular, otro_titular, mocker):
    mock_titular_principal = mocker.patch(
        'diario.models.cuenta.TITULAR_PRINCIPAL',
        otro_titular.sk
    )
    return mock_titular_principal


# Tests

def test_completa_campo_titular_con_titular_por_defecto(mock_titular_principal, otro_titular):
    cuenta = CuentaInteractiva(nombre='Efectivo', sk='e')
    cuenta.limpiar()
    assert cuenta.titular == otro_titular


def test_si_no_existe_el_titular_por_defecto_da_error_de_validacion(
        mock_titular_principal, otro_titular):
    otro_titular.delete()
    cuenta = CuentaInteractiva(nombre='Efectivo', sk='e')
    with pytest.raises(errors.ErrorTitularPorDefectoInexistente):
        cuenta.limpiar()


def test_cuenta_no_puede_cambiar_de_titular(cuenta, titular, otro_titular):
    cuenta.titular = otro_titular

    with pytest.raises(
            ErrorCambioEnCampoFijo,
            match="No se puede cambiar valor del campo 'titular'"
    ):
        cuenta.limpiar()


def test_cuenta_no_puede_tener_fecha_de_creacion_anterior_a_la_fecha_de_alta_de_su_titular(titular):
    cuenta = CuentaInteractiva(
        nombre='cuenta',
        sk='c',
        titular=titular,
        fecha_creacion=titular.fecha_alta-datetime.timedelta(1)
    )
    with pytest.raises(
            errors.ErrorFechaAnteriorAAltaTitular,
            match=re.escape(
                f"Fecha de creación de cuenta \"{cuenta.nombre}\" ({cuenta.fecha_creacion}) "
                f"anterior a fecha de alta de titular \"{titular.nombre}\" ({titular.fecha_alta})"
            )
    ):
        cuenta.limpiar()
