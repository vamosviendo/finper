import pytest

from diario.models import Movimiento


def test_devuelve_true_si_hay_cambio_en_alguno_de_los_campos_dados(entrada, importe_alto):
    entrada.importe = importe_alto
    assert entrada.cambia_campo('_importe', 'dia') is True


def test_devuelve_false_si_no_hay_cambio_en_ninguno_de_los_campos_dados(entrada, importe_alto):
    entrada.importe = importe_alto
    assert entrada.cambia_campo('concepto', 'dia') is False


def test_acepta_un_movimiento_contra_el_cual_comparar(entrada, importe_alto):
    mov2 = Movimiento(concepto='Otro concepto', importe=entrada.importe, cta_entrada=entrada.cta_entrada)
    assert entrada.cambia_campo('concepto', contraparte=mov2) is True
    assert entrada.cambia_campo('_importe', contraparte=mov2) is False


def test_da_error_si_recibe_campo_inexistente(entrada, importe_alto):
    with pytest.raises(ValueError):
        entrada.cambia_campo('importe')


def test_devuelve_true_si_el_movimiento_es_nuevo(cuenta):
    mov = Movimiento(concepto="Concepto", importe=252, cta_entrada=cuenta)
    assert mov.cambia_campo("concepto") is True
    assert mov.cambia_campo("_importe") is True
    assert mov.cambia_campo("cta_entrada") is True
    assert mov.cambia_campo("moneda") is True
