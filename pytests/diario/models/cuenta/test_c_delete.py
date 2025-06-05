import pytest

from utils import errors


def test_no_permite_eliminar_cuentas_con_saldo(cuenta_con_saldo):
    assert cuenta_con_saldo.saldo() != 0
    with pytest.raises(errors.SaldoNoCeroException):
        cuenta_con_saldo.delete()
