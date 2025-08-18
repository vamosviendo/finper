from diario.models import SaldoDiario


def test_devuelve_contenido_de_campo__importe(saldo_diario):
    assert saldo_diario.importe == saldo_diario._importe


def test_asigna_importe_a_campo__importe(cuenta, importe):
    saldo = SaldoDiario(cuenta=cuenta)
    saldo.importe = importe
    assert saldo._importe == importe


def test_redondea_valor_antes_de_asignarlo_a_campo__importe(cuenta):
    saldo = SaldoDiario(cuenta=cuenta, importe=154.588)
    assert saldo._importe == 154.59
