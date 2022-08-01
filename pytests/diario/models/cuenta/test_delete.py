import pytest

from utils import errors

pytestmark = pytest.mark.django_db


def test_no_permite_eliminar_cuentas_con_saldo(cuenta_con_saldo):
    with pytest.raises(errors.SaldoNoCeroException):
        cuenta_con_saldo.delete()
