import pytest

from diario.models import Movimiento, Cuenta
from utils.helpers_tests import dividir_en_dos_subcuentas

pytestmark = pytest.mark.django_db


def test_devuelve_false_si_cuenta_no_es_cuenta_credito(cuenta: Cuenta):
    assert not cuenta.es_cuenta_credito


def test_devuelve_true_si_cuenta_es_cuenta_credito(credito: Movimiento):
    cc2, cc1 = credito.recuperar_cuentas_credito()
    assert cc2.es_cuenta_credito
    assert cc1.es_cuenta_credito


# TODO: ¿qué onda este test? ¿Lo eliminamos?
def test_devuelve_false_si_cuenta_no_es_interactiva(cuenta: Cuenta):
    cuenta = dividir_en_dos_subcuentas(cuenta)
    assert not cuenta.es_cuenta_credito
