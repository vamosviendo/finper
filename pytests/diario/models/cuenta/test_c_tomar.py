from django.core.exceptions import FieldError, MultipleObjectsReturned

from diario.models import Cuenta, CuentaInteractiva, CuentaAcumulativa
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_tomar_devuelve_cuenta_de_la_clase_correcta(cuenta):
    cta_nueva = Cuenta.tomar(pk=cuenta.pk)
    assert isinstance(cta_nueva, CuentaInteractiva)

    cuenta = dividir_en_dos_subcuentas(cuenta)
    cta_acum_nueva = Cuenta.tomar(pk=cuenta.pk)
    assert isinstance(cta_acum_nueva, CuentaAcumulativa)


def test_permite_tomar_por_sk(cuenta, cuenta_2):
    try:
        m = Cuenta.tomar(sk=cuenta._sk)
    except (FieldError, MultipleObjectsReturned):
        raise AssertionError("No permite tomar por sk")
    assert m == cuenta
