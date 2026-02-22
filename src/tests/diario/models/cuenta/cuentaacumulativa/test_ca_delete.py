import pytest

from diario.models import Movimiento, Cuenta
from utils import errors


def test_no_permite_eliminar_cuenta_acumulativa_con_movimientos_anteriores_a_su_conversion(cuenta_con_saldo, fecha):
    Movimiento.crear(
        fecha=fecha,
        concepto="Puesta en cero",
        cta_salida=cuenta_con_saldo,
        importe=cuenta_con_saldo.saldo(),
    )

    assert cuenta_con_saldo.saldo() == 0
    movs_ccs = cuenta_con_saldo.movs()

    cuenta_con_saldo = cuenta_con_saldo.dividir_y_actualizar(
        ['subcuenta 1 con saldo', 'scs1', 60],
        ['subcuenta 2 con saldo', 'scs2'],
        fecha=fecha
    )

    assert list(cuenta_con_saldo.movs()) == list(movs_ccs)

    with pytest.raises(errors.ExistenMovimientosException):
        cuenta_con_saldo.delete()


def test_no_permite_eliminar_cuenta_acumulativa_con_subcuentas_con_movimientos(cuenta_acumulativa_saldo_0, fecha):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    Movimiento.crear(
        fecha=fecha,
        concepto="Movimiento de subcuenta",
        cta_entrada=sc1,
        importe=150
    )
    Movimiento.crear(
        fecha=fecha,
        concepto="Puesta en cero",
        cta_salida=sc1,
        importe=150
    )
    with pytest.raises(errors.ExistenMovimientosException):
        cuenta_acumulativa_saldo_0.delete()


def test_permite_eliminar_cuenta_acumulativos_sin_movimientos_propios_ni_de_subcuentas(cuenta_acumulativa_saldo_0):
    sk0 = cuenta_acumulativa_saldo_0.sk
    sk1, sk2 = [x.sk for x in cuenta_acumulativa_saldo_0.subcuentas.all()]
    cuenta_acumulativa_saldo_0.delete()
    assert not Cuenta.filtro(sk__in=[sk0, sk1, sk2]).exists()
