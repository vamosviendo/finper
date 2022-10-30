from diario.models import Saldo


def test_asigna_importe_a_campo__importe(cuenta, importe):
    saldo = Saldo(cuenta=cuenta)
    saldo.importe = importe
    assert saldo._importe == importe


def test_devuelve_contenido_de_campo__importe(saldo):
    assert saldo.importe == saldo._importe


def test_redondea_valor_antes_de_asignarlo_a_campo__importe(cuenta):
    saldo = Saldo(cuenta=cuenta, importe=154.588)
    assert saldo._importe == 154.59
