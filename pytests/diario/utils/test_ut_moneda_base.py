import pytest

from diario.utils import moneda_base
from utils import errors


@pytest.fixture
def mock_moneda_base(mocker, moneda):
    return mocker.patch('diario.utils.MONEDA_BASE', moneda.monname)


def test_devuelve_moneda_base_tomada_de_settings_app(moneda, moneda_2, mock_moneda_base):
    assert moneda_base() != moneda_2
    assert moneda_base() == moneda


def test_si_no_encuentra_moneda_base_tira_error_moneda_base_inexistente(moneda, moneda_2, mock_moneda_base):
    moneda.delete()
    with pytest.raises(errors.ErrorMonedaBaseInexistente):
        moneda_base()
