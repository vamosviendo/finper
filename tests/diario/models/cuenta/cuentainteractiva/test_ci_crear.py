import pytest

from diario.models import CuentaInteractiva, Movimiento, Cuenta


@pytest.fixture(autouse=True)
def titular_principal(titular_principal):
    return titular_principal


def test_llama_a_metodo_crear_de_clase_cuenta(mocker):
    mock_crear = mocker.patch('diario.models.cuenta.Cuenta.crear')
    CuentaInteractiva.crear('Cuenta Interactiva', 'ci')
    mock_crear.assert_called_once_with(
        nombre='Cuenta Interactiva', sk='ci', cta_madre=None, finalizar=True)


def test_genera_movimiento_inicial_si_se_pasa_argumento_saldo():
    cuenta = CuentaInteractiva.crear(nombre='Cuenta Interactiva', sk='ci', saldo=155)
    assert Movimiento.cantidad() == 1
    mov = Movimiento.primere()
    assert mov.concepto == f'Saldo inicial de {cuenta.nombre}'


def test_pasa_fecha_creacion_a_movimiento_inicial(mocker, fecha):
    mock_crear_mov = mocker.patch('diario.models.cuenta.Movimiento.crear')
    ANY = mocker.ANY
    CuentaInteractiva.crear(
        nombre='Cuenta Interactiva', sk='ci', saldo=155, fecha_creacion=fecha)
    mock_crear_mov.assert_called_once_with(
        concepto=ANY,
        importe=ANY,
        cta_entrada=ANY,
        fecha=fecha,
        moneda=ANY,
    )


def test_pasa_moneda_de_cuenta_creada_a_movimiento_inicial(mocker, fecha):
    mock_crear_mov = mocker.patch('diario.models.cuenta.Movimiento.crear')
    ANY = mocker.ANY
    ci = CuentaInteractiva.crear(
        nombre='Cuenta Interactiva', sk='ci', saldo=155, fecha_creacion=fecha)
    mock_crear_mov.assert_called_once_with(
        concepto=ANY,
        importe=ANY,
        cta_entrada=ANY,
        fecha=ANY,
        moneda=ci.moneda,
    )


def test_no_genera_movimiento_si_no_se_pasa_argumento_saldo():
    CuentaInteractiva.crear('Cuenta Interactiva', 'ci')
    assert Movimiento.cantidad() == 0


def test_no_genera_movimiento_si_argumento_saldo_es_igual_a_cero():
    CuentaInteractiva.crear('Cuenta Interactiva', 'ci', saldo=0)
    assert Movimiento.cantidad() == 0


def test_importe_de_movimiento_generado_coincide_con_argumento_saldo():
    CuentaInteractiva.crear('Cuenta Interactiva', 'ci', saldo=232)
    mov = Movimiento.primere()
    assert mov.importe == 232


def test_cuenta_creada_con_saldo_positivo_es_cta_entrada_del_movimiento_generado():
    cuenta = CuentaInteractiva.crear('Cuenta saldo positivo', 'csp', saldo=234)
    mov = Movimiento.primere()
    assert mov.cta_entrada == Cuenta.tomar(pk=cuenta.pk, polymorphic=False)


def test_cuenta_creada_con_saldo_negativo_es_cta_salida_del_movimiento_generado():
    cuenta = CuentaInteractiva.crear('Cuenta saldo negativo', 'csn', saldo=-354)
    mov = Movimiento.primere()
    assert mov.cta_entrada is None
    assert mov.cta_salida == Cuenta.tomar(pk=cuenta.pk, polymorphic=False)
    assert mov.importe == 354


def test_puede_pasarse_saldo_en_formato_str():
    cuenta = CuentaInteractiva.crear('Cuenta con saldo', 'ccs', saldo='354')
    assert cuenta.saldo() == 354


def test_no_genera_movimiento_con_saldo_cero_en_formato_str():
    CuentaInteractiva.crear('Cuenta saldo cero', 'csc', saldo='0')
    assert Movimiento.cantidad() == 0
