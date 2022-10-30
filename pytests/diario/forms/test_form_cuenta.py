from diario.forms import FormCuenta


def test_no_acepta_cuentas_sin_slug():
    formcta = FormCuenta(data={'nombre': 'Efectivo'})
    assert not formcta.is_valid()


def test_no_acepta_guion_bajo_inicial_en_slug():
    formcta = FormCuenta(data={'nombre': '_Efectivo', 'slug': '_efe'})
    assert not formcta.is_valid()
