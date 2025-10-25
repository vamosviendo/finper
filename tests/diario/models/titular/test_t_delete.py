import pytest

from diario.models import Movimiento, Cuenta, Titular
from utils import errors


def test_no_permite_eliminar_titulares_con_capital(titular, entrada):
    with pytest.raises(errors.SaldoNoCeroException):
        titular.delete()


def test_no_permite_eliminar_titulares_con_cuentas_con_movimientos(titular, cuenta, entrada, fecha):
    Movimiento.crear(
        fecha=fecha,
        concepto="Puesta en cero",
        importe=entrada.importe,
        cta_salida=cuenta,
    )
    with pytest.raises(errors.ExistenMovimientosException):
        titular.delete()


def test_permite_eliminar_titulares_sin_cuentas_con_movimientos(titular, cuenta):
    sk_cuenta = cuenta.sk
    sk_titular = titular.sk
    titular.delete()
    assert not Cuenta.filtro(sk=sk_cuenta).exists()
    assert not Titular.filtro(sk=sk_titular).exists()


def test_permite_eliminar_titulares_con_cuentas_con_movimientos_si_se_eliminan_antes_los_movimientos(
        titular, cuenta, entrada):
    sk_tit = titular.sk
    sk_cta = cuenta.sk
    entrada.delete()
    titular.delete()
    assert not Cuenta.filtro(sk=sk_cta).exists()
    assert not Titular.filtro(sk=sk_tit).exists()
