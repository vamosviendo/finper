import pytest

from diario.models import Movimiento


def test_devuelve_true_si_hay_cambio_en_todos_los_campos_dados(entrada, importe_alto):
    entrada.importe = importe_alto
    entrada.concepto = "Concepto cambiado"
    assert entrada.cambian_campos('_importe', 'concepto') is True


def test_devuelve_false_si_no_hay_cambio_en_alguno_de_los_campos_dados(entrada, importe_alto):
    entrada.importe = importe_alto
    assert entrada.cambian_campos('concepto', '_importe') is False


def test_acepta_un_movimiento_contra_el_cual_comparar(entrada, importe_alto):
    mov2 = Movimiento(concepto='Otro concepto', importe=2546, cta_entrada=entrada.cta_entrada)
    assert entrada.cambian_campos('concepto', '_importe', contraparte=mov2) is True
    assert entrada.cambian_campos('concepto', 'cta_entrada', contraparte=mov2) is False


def test_da_error_si_recibe_campo_inexistente(entrada, importe_alto):
    with pytest.raises(ValueError):
        entrada.cambian_campos('_importe', 'cuchuflo')
