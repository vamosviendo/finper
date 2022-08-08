from datetime import timedelta, date

import pytest
from django.core.exceptions import ValidationError

from diario.models import CuentaAcumulativa


@pytest.fixture
def nueva_fecha(cuenta_acumulativa: CuentaAcumulativa) -> date:
    return cuenta_acumulativa.fecha_conversion + timedelta(10)


def test_permite_cambiar_fecha_de_conversion_de_cuenta_por_fecha_posterior(cuenta_acumulativa, nueva_fecha):
    cuenta_acumulativa.fecha_conversion = nueva_fecha
    cuenta_acumulativa.full_clean()
    cuenta_acumulativa.save()

    assert cuenta_acumulativa.fecha_conversion == nueva_fecha


def test_si_se_modifica_fecha_de_conversion_de_cuenta_se_modifica_fecha_de_movimientos_de_traspaso_de_saldo(
        cuenta_acumulativa, nueva_fecha):
    cuenta_acumulativa.fecha_conversion = nueva_fecha
    cuenta_acumulativa.full_clean()
    cuenta_acumulativa.save()

    mov1, mov2 = cuenta_acumulativa.movs_conversion()
    assert mov1.fecha == nueva_fecha
    assert mov2.fecha == nueva_fecha


def test_no_permite_cambiar_fecha_de_conversion_por_una_anterior_a_la_de_cualquier_movimiento_de_la_cuenta(
        cuenta, entrada):
    cuentaacumulativa = cuenta.dividir_y_actualizar(
        ['subcuenta 1 con saldo', 'scs1', 60],
        ['subcuenta 2 con saldo', 'scs2'],
        fecha=entrada.fecha + timedelta(10)
    )
    cuentaacumulativa.fecha_conversion = entrada.fecha - timedelta(1)
    with pytest.raises(ValidationError):
        cuentaacumulativa.full_clean()
