from diario.models import CuentaInteractiva, Titular
from diario.settings_app import TITULAR_PRINCIPAL


def test_se_relaciona_con_titular(titular):
    cuenta = CuentaInteractiva(nombre='cuenta', slug='cta')
    cuenta.titular = titular
    cuenta.full_clean()
    cuenta.save()
    assert cuenta.titular == titular


def test_toma_titular_por_defecto():
    cuenta = CuentaInteractiva(nombre='cuenta', slug='cta')

    cuenta.full_clean()
    cuenta.save()

    assert cuenta.titular == Titular.tomar(titname=TITULAR_PRINCIPAL['titname'])

