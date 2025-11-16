from datetime import date

import pytest
from django.core.exceptions import ValidationError

from diario.models import Moneda, Cotizacion


@pytest.mark.nomonbase
def test_guarda_y_recupera_monedas(mock_moneda_base):
    moneda = Moneda()
    moneda.nombre = "Moneda"
    moneda.sk = "mn"
    # moneda.cotizacion = 1.5
    moneda.clean_save()

    assert Moneda.cantidad() == 1
    mon = Moneda.tomar(sk="mn")
    assert mon.nombre == "Moneda"
    # assert mon.cotizacion == 1.5


def test_no_se_permiten_nombres_repetidos(peso):
    mon2 = Moneda(nombre=peso.nombre, sk="otra")
    with pytest.raises(ValidationError):
        mon2.full_clean()


def test_no_se_permiten_sks_repetidos(peso):
    mon2 = Moneda(nombre='Moneda 2', sk=peso.sk)
    with pytest.raises(ValidationError):
        mon2.full_clean()


def test_natural_key_devuelve_id_basada_en_sk(peso):
    assert peso.natural_key() == (peso.sk, )
