import pytest

from diario.utils.utils_moneda import moneda_base, id_moneda_base
from utils import errors


class TestMonedaBase:
    def test_devuelve_moneda_base_tomada_de_settings_app(self, peso, dolar, mock_moneda_base):
        assert moneda_base() != dolar
        assert moneda_base() == peso

    def test_si_no_encuentra_moneda_base_tira_error_moneda_base_inexistente(self, peso, dolar, mock_moneda_base):
        peso.delete()
        with pytest.raises(errors.ErrorMonedaBaseInexistente):
            moneda_base()


class TestIdMonedaBase:
    def test_devuelve_id_de_moneda_base_tomada_de_settings_app(self, peso, dolar, mock_moneda_base):
        assert id_moneda_base() != dolar.id
        assert id_moneda_base() == peso.id
