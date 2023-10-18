from diario.models import CuentaInteractiva


def test_se_relaciona_con_titular(titular):
    cuenta = CuentaInteractiva(nombre='cuenta', slug='cta')
    cuenta.titular = titular
    cuenta.full_clean()
    cuenta.save()
    assert cuenta.titular == titular
