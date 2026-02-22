from django.core.exceptions import FieldError

from diario.models import Cuenta


def test_permite_filtrar_por_sk(cuenta, cuenta_2):
    try:
        cuentas = Cuenta.filtro(sk=cuenta.sk)
    except FieldError:
        raise AssertionError("No permite filtrar por sk")
    assert list(cuentas) == [cuenta]
