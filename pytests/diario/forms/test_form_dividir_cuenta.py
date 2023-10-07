from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from diario.forms import FormDividirCuenta
from diario.models import CuentaInteractiva, Titular


@pytest.fixture
def form(cuenta_con_saldo: CuentaInteractiva, otro_titular: Titular) -> FormDividirCuenta:
    return FormDividirCuenta(
        data={
            'form_0_nombre': 'Subcuenta 1',
            'form_0_slug': 'sc1',
            'form_0_saldo': 50,
            'form_0_titular': cuenta_con_saldo.titular,
            'form_1_nombre': 'Subcuenta 2',
            'form_1_slug': 'sc2',
            'form_1_saldo': cuenta_con_saldo.saldo - 50,
            'form_1_titular': otro_titular,
            'form_1_esgratis': True,
        },
        cuenta=cuenta_con_saldo.slug,
    )


@pytest.fixture
def subcuentas(cuenta_con_saldo: CuentaInteractiva, otro_titular: Titular) -> List[Dict[str, Any]]:
    return [
            {
                'nombre': 'Subcuenta 1',
                'slug': 'sc1',
                'saldo': 50.0,
                'titular': cuenta_con_saldo.titular,
                'esgratis': False,
            }, {
                'nombre': 'Subcuenta 2',
                'slug': 'sc2',
                'saldo': cuenta_con_saldo.saldo - 50.0,
                'titular': otro_titular,
                'esgratis': True,
            },
        ]


@pytest.fixture
def mock_crear_movimiento_credito(mocker) -> MagicMock:
    return mocker.patch(
        'diario.forms.Movimiento._crear_movimiento_credito', autospec=True
    )


@pytest.fixture
def mock_dividir_y_actualizar(mocker) -> MagicMock:
    return mocker.patch(
        'diario.forms.CuentaInteractiva.dividir_y_actualizar'
    )


def test_save_divide_cuenta(mocker, form, cuenta_con_saldo, subcuentas):
    mock_dividir_entre = mocker.patch('diario.forms.CuentaInteractiva.dividir_entre', autospec=True)
    form.is_valid()
    form.save()
    mock_dividir_entre.assert_called_once_with(cuenta_con_saldo, *subcuentas, fecha=None)


def test_save_llama_a_clean(mocker, form, subcuentas):
    mock_clean = mocker.patch('diario.forms.FormDividirCuenta.clean')

    def side_effect():
        form.subcuentas = subcuentas
    mock_clean.side_effect = side_effect

    form.is_valid()
    form.save()
    mock_clean.assert_called_once()


def test_save_devuelve_cuenta_madre(mock_dividir_y_actualizar, cuenta_con_saldo, form):
    mock_dividir_y_actualizar.return_value = cuenta_con_saldo
    form.is_valid()
    cuenta = form.save()
    assert cuenta == cuenta_con_saldo
