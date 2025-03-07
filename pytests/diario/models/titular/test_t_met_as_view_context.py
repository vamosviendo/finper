import pytest


@pytest.fixture
def context(titular):
    return titular.as_view_context()


def test_incluye_titname(titular, context):
    assert context.get('titname') is not None
    assert context['titname'] == titular.titname


def test_incluye_nombre(titular, context):
    assert context.get('nombre') is not None
    assert context['nombre'] == titular.nombre


def test_incluye_capital_del_titular(entrada, context):
    titular = entrada.cta_entrada.titular
    assert context['capital'] == titular.capital


def test_cuentas_del_titular_se_ordenan_por_nombre(titular, cuenta_2, cuenta):
    context = titular.as_view_context(es_elemento_principal=True)
    assert \
        list(context['cuentas']) == \
        [x for x in (cuenta, cuenta_2)]


def test_incluye_movimientos_del_titular_en_formato_dict(
        entrada, salida, traspaso, entrada_cuenta_ajena, context):
    assert context['movimientos'] == [x.as_view_context() for x in [entrada, salida, traspaso]]


def test_incluye_dias_con_movimientos_de_cuentas_del_titular(
        dia, dia_posterior, dia_tardio,
        entrada, salida, entrada_posterior_cuenta_ajena, salida_tardia_tercera_cuenta,
        context):
    assert list(context['dias']) == [dia_tardio, dia]


def test_si_recibe_movimiento_incluye_solo_movimientos_de_cuentas_del_titular_como_dict(
        entrada, salida, entrada_cuenta_ajena):
    titular = entrada.cta_entrada.titular
    context = titular.as_view_context(entrada)
    assert context['movimientos'] == [x.as_view_context() for x in [entrada, salida]]


def test_si_recibe_movimiento_incluye_capital_historico_de_titular_en_movimiento_como_capital(
        entrada, salida, entrada_otra_cuenta):
    titular = entrada.cta_entrada.titular
    context = titular.as_view_context(entrada)
    assert context['capital'] == titular.capital_historico(entrada)


def test_si_recibe_movimiento_incluye_saldo_historico_de_cuentas_del_titular(
        cuenta, cuenta_2, entrada, salida):
    titular = cuenta.titular
    context = titular.as_view_context(entrada, es_elemento_principal=True)
    print(f"CONTEXT CUENTAS: {context['cuentas']}")
    print(x.as_view_context(entrada) for x in (cuenta, cuenta_2))

    assert \
        [x.saldo_en_mov(entrada) for x in context['cuentas']] == \
        [x.as_view_context(entrada)['saldo'] for x in (cuenta, cuenta_2)]


def test_si_es_elemento_principal_incluye_cuentas_del_titular(
        titular, cuenta, cuenta_2, cuenta_ajena):
    context = titular.as_view_context(es_elemento_principal=True)
    assert list(context['cuentas']) == [cuenta, cuenta_2]


def test_si_no_es_elemento_principal_no_incluye_saldo_gral(titular):
    context = titular.as_view_context(es_elemento_principal=False)
    assert 'saldo_gral' not in context.keys()


def test_si_no_es_elemento_principal_no_incluye_cuentas_del_titular(titular):
    context = titular.as_view_context(es_elemento_principal=False)
    assert 'cuentas' not in context.keys()
