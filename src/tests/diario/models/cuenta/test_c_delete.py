import pytest

from diario.models import Movimiento, Cuenta
from utils import errors


def test_no_permite_eliminar_cuentas_con_saldo(cuenta_con_saldo):
    with pytest.raises(errors.SaldoNoCeroException):
        cuenta_con_saldo.delete()


def test_no_permite_eliminar_cuenta_con_movimientos_aunque_el_saldo_sea_cero(cuenta_con_saldo, fecha):
    Movimiento.crear(
        fecha=fecha,
        concepto="Puesta en cero",
        cta_salida=cuenta_con_saldo,
        importe=cuenta_con_saldo.saldo(),
    )
    with pytest.raises(errors.ExistenMovimientosException):
        cuenta_con_saldo.delete()


def test_puede_eliminarse_cuenta_con_movimientos_en_el_caso_de_conversion_en_acumulativa(cuenta_con_saldo, fecha):
    Movimiento.crear(
        fecha=fecha,
        concepto="Puesta en cero",
        cta_salida=cuenta_con_saldo,
        importe=cuenta_con_saldo.saldo(),
    )
    cuenta_con_saldo.delete(esta_siendo_convertida=True)


def test_permite_eliminar_cuenta_sin_movimientos(cuenta):
    sk = cuenta.sk
    cuenta.delete()
    assert not Cuenta.filtro(sk=sk).exists()


def test_permite_eliminar_cuenta_con_movimientos_si_se_eliminan_antes_los_movimientos(cuenta, entrada):
    sk = cuenta.sk
    entrada.delete()
    cuenta.delete()
    assert not Cuenta.filtro(sk=sk).exists()
