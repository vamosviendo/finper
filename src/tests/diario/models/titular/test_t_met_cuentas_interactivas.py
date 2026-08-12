from django.db import models


def test_devuelve_solo_cuentas_interactivas_del_titular(titular, cuenta, cuenta_2):
    resultado = titular.cuentas_interactivas()
    assert isinstance(resultado, models.QuerySet)
    assert set(resultado) == {cuenta, cuenta_2}


def test_excluye_cuentas_de_otros_titulares(titular, otro_titular, cuenta, cuenta_ajena):
    assert cuenta_ajena not in titular.cuentas_interactivas()
