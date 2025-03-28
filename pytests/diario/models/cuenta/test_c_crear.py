from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from diario.models import Cuenta, CuentaInteractiva


def test_crea_cuenta(titular):
    Cuenta.crear(nombre='Efectivo', slug='e', titular=titular)
    assert Cuenta.cantidad() == 1


@patch('diario.models.cuenta.CuentaInteractiva.crear')
def test_llama_a_metodo_crear_de_clase_CuentaInteractiva(mock_crear):
    Cuenta.crear(nombre='Efectivo', slug='e')
    mock_crear.assert_called_once_with(
        nombre='Efectivo', slug='e', cta_madre=None)


def test_cuenta_creada_es_interactiva(cuenta):
    assert isinstance(cuenta, CuentaInteractiva)


def test_devuelve_cuenta_creada(titular):
    cuenta = Cuenta.crear(nombre='Efectivo', slug='E', titular=titular)
    assert (
        cuenta.nombre, cuenta.slug, cuenta.titular
    ) == (
        'efectivo', 'e', titular
    )


def test_no_permite_nombre_vacio():
    with pytest.raises(ValidationError):
        Cuenta.crear(nombre=None, slug='E')


def test_no_permite_slug_vacio():
    with pytest.raises(ValidationError):
        Cuenta.crear(nombre='Cuenta', slug=None)
