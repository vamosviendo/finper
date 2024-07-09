from datetime import date

import pytest
from django.core.exceptions import ValidationError

from diario.models import Moneda, Cotizacion


@pytest.mark.nomonbase
def test_guarda_y_recupera_monedas(mock_moneda_base):
    moneda = Moneda()
    moneda.nombre = "Moneda"
    moneda.monname = "mn"
    # moneda.cotizacion = 1.5
    moneda.full_clean()
    moneda.save()

    assert Moneda.cantidad() == 1
    mon = Moneda.tomar(monname="mn")
    assert mon.nombre == "Moneda"
    # assert mon.cotizacion == 1.5


def test_no_se_permiten_nombres_repetidos(peso):
    mon2 = Moneda(nombre=peso.nombre, monname="otra", cotizacion=2)
    with pytest.raises(ValidationError):
        mon2.full_clean()


def test_no_se_permiten_monnames_repetidos(peso):
    mon2 = Moneda(nombre='Moneda 2', monname=peso.monname, cotizacion=2)
    with pytest.raises(ValidationError):
        mon2.full_clean()


def test_natural_key_devuelve_id_basada_en_monname(peso):
    assert peso.natural_key() == (peso.monname, )
