import pytest

from diario.models import Movimiento, Titular


@pytest.fixture
def context(cuenta):
    return cuenta.as_view_context(es_elemento_principal=True)


def test_incluye_nombre_de_cuenta(context, cuenta):
    assert context.get('nombre') is not None
    assert context['nombre'] == cuenta.nombre


def test_incluye_slug_de_cuenta_como_clave_ctaname(context, cuenta):
    assert context.get('ctaname') is not None
    assert context['ctaname'] == cuenta.slug


def test_incluye_fecha_de_creacion_de_cuenta(context, cuenta):
    assert context.get('fecha_alta') is not None
    assert context['fecha_alta'] == cuenta.fecha_creacion


def test_incluye_moneda_como_dict(context, cuenta):
    assert context.get('moneda') is not None
    assert context['moneda'] == cuenta.moneda.as_view_context()


def test_si_cuenta_es_interactiva_incluye_lista_con_titular_de_cuenta_en_formato_dict_como_titulares(
        context, cuenta):
    assert context['titulares'] == [cuenta.titular.as_view_context()]


def test_si_cuenta_es_interactiva_y_recibe_movimiento_incluye_capital_historico_como_capital_del_titular(
        cuenta, entrada, salida):
    context = cuenta.as_view_context(entrada)
    assert context['titulares'][0]['capital'] == cuenta.titular.capital_historico(entrada)


def test_incluye_dict_de_saldos_expresados_en_distintas_monedas(cuenta_con_saldo, peso, dolar, euro):
    context = cuenta_con_saldo.as_view_context()
    assert context.get('saldos') is not None
    assert type(context['saldos']) is dict
    for moneda in (peso, dolar, euro):
        assert context['saldos'][moneda.monname] == cuenta_con_saldo.saldo_en(moneda)


def test_si_cuenta_es_acumulativa_incluye_subcuentas_en_formato_dict(cuenta_acumulativa):
    context = cuenta_acumulativa.as_view_context(es_elemento_principal=True)
    assert \
        list(context['cuentas']) == [
            x.as_view_context()
            for x in cuenta_acumulativa.subcuentas.all()
        ]


def test_si_cuenta_es_acumulativa_clave_es_acumulativa_es_True(cuenta_acumulativa):
    context = cuenta_acumulativa.as_view_context(es_elemento_principal=True)
    assert context['es_acumulativa'] is True


def test_si_cuenta_es_interactiva_clave_es_acumulativa_es_False(context):
    assert context['es_acumulativa'] is False


def test_si_cuenta_es_acumulativa_y_recibe_movimiento_toma_saldo_en_mov_de_subcuentas_como_saldo(
        cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    entrada = Movimiento.crear('entrada', 23, cta_entrada=sc1)
    Movimiento.crear('salida', 12, cta_salida=sc1)

    context = cuenta_acumulativa.as_view_context(entrada)

    assert sc1.saldo_en_mov(entrada) != sc1.saldo
    assert context['cuentas'][0]['saldo'] == sc1.saldo_en_mov(entrada)


def test_si_cuenta_es_acumulativa_incluye_lista_de_titulares_de_la_cuenta_en_formato_dict(
        cuenta_de_dos_titulares):
    context = cuenta_de_dos_titulares.as_view_context(es_elemento_principal=True)
    assert context['titulares'] == [
        x.as_view_context() for x in cuenta_de_dos_titulares.titulares]


def test_si_cuenta_es_acumulativa_y_recibe_movimiento_toma_capital_historico_como_capital_de_titulares(
        cuenta_de_dos_titulares):
    sc1, sc2 = cuenta_de_dos_titulares.subcuentas.all()
    entrada = Movimiento.crear('entrada en subcuenta', 80, cta_entrada=sc1)
    Movimiento.crear('otra entrada en subcuenta', 30, cta_entrada=sc1)
    Movimiento.crear('entrada en otra subcuenta', 50, cta_entrada=sc2)
    context = cuenta_de_dos_titulares.as_view_context(entrada)
    for titular in context['titulares']:
        assert \
            titular['capital'] == \
            Titular.tomar(titname=titular['titname']).capital_historico(entrada)


def test_incluye_movimientos_de_la_cuenta_como_dict(cuenta, entrada, salida, entrada_otra_cuenta):
    context = cuenta.as_view_context(es_elemento_principal=True)
    assert context['movimientos'] == [x.as_view_context() for x in[entrada, salida]]


def test_incluye_solamente_dias_en_los_que_hay_movimientos_de_la_cuenta(
        cuenta, dia, dia_posterior, dia_tardio,
        entrada, entrada_posterior_otra_cuenta, entrada_tardia):
    context = cuenta.as_view_context()
    assert context['dias'] == [dia_tardio, dia]


def test_si_cuenta_es_acumulativa_incluye_subcuentas_como_cuentas_en_formato_dict(cuenta_acumulativa):
    context = cuenta_acumulativa.as_view_context(es_elemento_principal=True)
    assert context['cuentas'] == [
        x.as_view_context()
        for x in cuenta_acumulativa.subcuentas.all()
    ]


def test_si_cuenta_es_interactiva_incluye_lista_vacia_como_cuentas(context, cuenta):
    assert len(context['cuentas']) == 0


def test_si_recibe_movimiento_incluye_saldo_historico_de_cuenta_en_movimiento_como_saldo(
        entrada, salida, salida_posterior):
    cuenta = entrada.cta_entrada
    context = cuenta.as_view_context(movimiento=salida)
    assert context.get('saldo') is not None
    assert context['saldo'] == cuenta.saldo_en_mov(salida)


def test_si_recibe_movimiento_incluye_saldos_historicos_de_cuenta_en_movimiento_en_dict_de_saldos(
        entrada, salida, salida_posterior, peso, dolar, euro):
    cuenta = entrada.cta_entrada
    context = cuenta.as_view_context(movimiento=salida)
    for moneda in (peso, dolar, euro):
        assert context['saldos'][moneda.monname] == cuenta.saldo_en_mov_en(salida, moneda)


def test_si_cuenta_es_elemento_principal_y_tiene_madre_incluye_lista_de_dicts_de_ancestro_con_nombre_y_saldo(subsubcuenta):
    context = subsubcuenta.as_view_context(es_elemento_principal=True)
    assert context.get('ancestros') is not None
    assert \
        [x['nombre'] for x in context['ancestros']] == \
        [x.nombre for x in reversed(subsubcuenta.ancestros())]
    assert \
        [x['saldo'] for x in context['ancestros']] == \
        [x.saldo for x in reversed(subsubcuenta.ancestros())]


def test_si_cuenta_es_elemento_principal_y_tiene_madre_incluye_lista_de_dicts_de_cuentas_hermanas_con_nombre_y_saldo(
        subsubcuenta):
    madre = subsubcuenta.cta_madre
    madre.agregar_subcuenta('subsubcuenta 3', 'ssc3', subsubcuenta.titular)
    context = subsubcuenta.as_view_context(es_elemento_principal=True)
    assert context.get('hermanas') is not None
    assert \
        [x['nombre'] for x in context['hermanas']] == \
        [x.nombre for x in subsubcuenta.hermanas()]
    assert \
        [x['saldo'] for x in context['hermanas']] == \
        [x.saldo for x in subsubcuenta.hermanas()]


def test_si_cuenta_con_madre_no_es_elemento_principal_no_incluye_lista_de_dicts_de_ancestros_ni_cuentas_hermanas(
        subsubcuenta):
    context = subsubcuenta.as_view_context(es_elemento_principal=False)
    with pytest.raises(KeyError):
        print(context['hermanas'])
    with pytest.raises(KeyError):
        print(context['ancestros'])


def test_si_cuenta_es_elemento_principal_y_no_tiene_madre_no_incluye_lista_de_dicts_de_ancestros_ni_cuentas_hermanas(
        cuenta):
    context = cuenta.as_view_context(es_elemento_principal=True)
    with pytest.raises(KeyError):
        print(context['hermanas'])
    with pytest.raises(KeyError):
        print(context['ancestros'])


def test_si_cuenta_es_elemento_principal_y_tiene_madre_y_recibe_movimiento_incluye_lista_de_dicts_de_ancestro_con_nombre_y_saldo_historico(
        subsubcuenta, entrada):
    context = subsubcuenta.as_view_context(movimiento=entrada, es_elemento_principal=True)
    assert \
        [x['saldo'] for x in context['ancestros']] == \
        [x.saldo_en_mov(entrada) for x in reversed(subsubcuenta.ancestros())]


def test_si_cuenta_es_elemento_principal_y_tiene_madre_y_recibe_movimiento_incluye_lista_de_dicts_de_hermana_con_nombre_y_saldo_historico(
        subsubcuenta, entrada, salida):
    context = subsubcuenta.as_view_context(movimiento=entrada, es_elemento_principal=True)
    assert \
        [x['saldo'] for x in context['hermanas']] == \
        [x.saldo_en_mov(entrada) for x in subsubcuenta.hermanas()]
