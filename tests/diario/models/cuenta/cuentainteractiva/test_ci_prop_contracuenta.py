def test_devuelve_contenido_de_campo_contracuenta_en_cuenta_credito_de_deudor(cuenta_credito_deudor):
    assert cuenta_credito_deudor.contracuenta == cuenta_credito_deudor._contracuenta


def test_devuelve_contenido_de_campo_relacionado_con_contracuenta_en_cuenta_credito_de_acreedor(cuenta_credito_acreedor):
    assert cuenta_credito_acreedor.contracuenta == cuenta_credito_acreedor._cuentacontra


def test_devuelve_none_si_cuenta_no_es_de_credito(cuenta):
    assert cuenta.contracuenta is None
