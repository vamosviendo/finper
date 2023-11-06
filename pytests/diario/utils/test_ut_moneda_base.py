import pytest

from diario.utils import moneda_base
from utils import errors


@pytest.fixture
def mock_moneda_base(mocker, peso):
    return mocker.patch('diario.utils.MONEDA_BASE', peso.monname)


def test_devuelve_moneda_base_tomada_de_settings_app(peso, dolar, mock_moneda_base):
    assert moneda_base() != dolar
    assert moneda_base() == peso


def test_si_no_encuentra_moneda_base_tira_error_moneda_base_inexistente(peso, dolar, mock_moneda_base):
    peso.delete()
    with pytest.raises(errors.ErrorMonedaBaseInexistente):
        moneda_base()
