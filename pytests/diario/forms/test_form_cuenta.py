from datetime import date

from diario.forms import FormCuenta


def test_no_acepta_cuentas_sin_slug():
    formcta = FormCuenta(data={'nombre': 'Efectivo'})
    assert not formcta.is_valid()


def test_no_acepta_guion_bajo_inicial_en_slug():
    formcta = FormCuenta(data={'nombre': '_Efectivo', 'slug': '_efe'})
    assert not formcta.is_valid()


def test_muestra_campo_fecha_creacion():
    formcta = FormCuenta()
    assert 'fecha_creacion' in formcta.fields.keys()


def test_campo_fecha_creacion_muestra_fecha_actual_como_valor_por_defecto():
    formcta = FormCuenta()
    assert formcta.fields['fecha_creacion'].initial == date.today()
