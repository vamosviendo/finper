import pytest

from utils import errors


def test_no_permite_eliminar_titulares_con_capital(titular, entrada):
    with pytest.raises(errors.SaldoNoCeroException):
        titular.delete()
