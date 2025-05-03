import pytest
from django.core.exceptions import ValidationError

from diario.models import SaldoDiario

def test_puede_guardar_cuenta_dia_e_importe(cuenta, dia):
    saldo_diario = SaldoDiario(cuenta=cuenta, dia=dia, _importe=100)
    saldo_diario.save()
    assert saldo_diario.cuenta == cuenta
    assert saldo_diario.dia == dia
    assert saldo_diario._importe == 100


def test_hay_solo_un_saldo_diario_por_cuenta_en_un_dia(cuenta, cuenta_2, dia):
    SaldoDiario.crear(cuenta=cuenta, dia=dia, _importe=100)
    with pytest.raises(ValidationError):
        SaldoDiario.crear(cuenta=cuenta, dia=dia, _importe=90)

def test_saldos_se_ordenan_por_dia(cuenta, dia, dia_anterior, dia_posterior):
    sd = SaldoDiario.crear(cuenta=cuenta, dia=dia, _importe=1)
    sd_anterior = SaldoDiario.crear(cuenta=cuenta, dia=dia_anterior, _importe=1)
    sd_posterior = SaldoDiario.crear(cuenta=cuenta, dia=dia_posterior, _importe=1)
    assert [*SaldoDiario.todes()] == [sd_anterior, sd, sd_posterior]
