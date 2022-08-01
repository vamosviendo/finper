import pytest

from diario.models import Cuenta, CuentaInteractiva, CuentaAcumulativa
from utils.helpers_tests import dividir_en_dos_subcuentas

pytestmark = pytest.mark.django_db


def test_tomar_devuelve_cuenta_de_la_clase_correcta(cuenta):
    cta_nueva = Cuenta.tomar(pk=cuenta.pk)
    assert isinstance(cta_nueva, CuentaInteractiva)

    cuenta = dividir_en_dos_subcuentas(cuenta)
    cta_acum_nueva = Cuenta.tomar(pk=cuenta.pk)
    assert isinstance(cta_acum_nueva, CuentaAcumulativa)