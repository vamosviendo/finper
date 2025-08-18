from diario.models import CuentaInteractiva


def test_se_relaciona_con_titular(titular):
    cuenta = CuentaInteractiva(nombre='cuenta', sk='cta')
    cuenta.titular = titular
    cuenta.clean_save()
    assert cuenta.titular == titular
