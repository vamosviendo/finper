import pytest


@pytest.fixture
def context(cuenta):
    return cuenta.as_template_context()


def test_cuenta_se_incluye_a_si_misma(context, cuenta):
    assert context.get('cuenta') is not None
    assert context['cuenta'] == cuenta


def test_incluye_nombre_de_cuenta(context, cuenta):
    assert context.get('nombre') is not None
    assert context['nombre'] == cuenta.nombre


def test_si_cuenta_es_interactiva_incluye_lista_con_titular_de_cuenta_como_titulares(context, cuenta):
    assert list(context['titulares']) == [cuenta.titular]


def test_si_cuenta_es_acumulativa_pasa_lista_de_titulares_de_la_cuenta(cuenta_de_dos_titulares):
    context = cuenta_de_dos_titulares.as_template_context()
    assert list(context['titulares']) == cuenta_de_dos_titulares.titulares


def test_incluye_saldo_de_cuenta_como_saldo_general(cuenta_con_saldo):
    context = cuenta_con_saldo.as_template_context()
    assert context['saldo_gral'] == cuenta_con_saldo.saldo


def test_incluye_movimientos_de_la_cuenta(cuenta, entrada, salida, entrada_otra_cuenta):
    context = cuenta.as_template_context()
    assert list(context['movimientos']) == [entrada, salida]


def test_si_cuenta_es_acumulativa_incluye_sub_subcuentas_como_cuentas(cuenta_acumulativa):
    context = cuenta_acumulativa.as_template_context()
    assert list(context['cuentas']) == list(cuenta_acumulativa.subcuentas.all())


def test_si_cuenta_es_interactiva_incluye_queryset_vacio_como_cuentas(context, cuenta):
    assert context['cuentas'].count() == 0


def test_incluye_titulo_de_saldo_gral_con_cuenta(context, cuenta):
    assert context['titulo_saldo_gral'] == f"Saldo de {cuenta.nombre}"


def test_si_cuenta_tiene_madre_incluye_lista_de_dicts_de_ancestro_con_nombre_y_saldo(subsubcuenta):
    context = subsubcuenta.as_template_context()
    assert context.get('ancestros') is not None
    assert \
        [x['nombre'] for x in context['ancestros']] == \
        [x.nombre for x in reversed(subsubcuenta.ancestros())]
    assert \
        [x['saldo_gral'] for x in context['ancestros']] == \
        [x.saldo for x in reversed(subsubcuenta.ancestros())]


def test_si_cuenta_tiene_madre_incluye_lista_de_dicts_de_cuentas_hermanas_con_nombre_y_saldo(subsubcuenta):
    madre = subsubcuenta.cta_madre
    madre.agregar_subcuenta('subsubcuenta 3', 'ssc3', subsubcuenta.titular)
    context = subsubcuenta.as_template_context()
    assert context.get('hermanas') is not None
    assert \
        [x['nombre'] for x in context['hermanas']] == \
        [x.nombre for x in subsubcuenta.hermanas()]
    assert \
        [x['saldo_gral'] for x in context['hermanas']] == \
        [x.saldo for x in subsubcuenta.hermanas()]


def test_si_recibe_movimiento_incluye_movimiento_recibido(entrada, salida, client):
    cuenta = entrada.cta_entrada
    context = cuenta.as_template_context(movimiento=salida)
    assert context.get('movimiento') is not None
    assert context['movimiento'] == salida


def test_si_recibe_movimiento_incluye_saldo_historico_de_cuenta_en_movimiento_como_saldo_gral(
        entrada, salida, salida_posterior):
    cuenta = entrada.cta_entrada
    context = cuenta.as_template_context(movimiento=salida)
    assert context.get('saldo_gral') is not None
    assert context['saldo_gral'] == cuenta.saldo_en_mov(salida)


def test_si_recibe_movimiento_incluye_titulo_de_saldo_historico_con_cuenta_y_movimiento(entrada):
    cuenta = entrada.cta_entrada
    context = cuenta.as_template_context(movimiento=entrada)
    assert (
        context['titulo_saldo_gral'] ==
        f'Saldo de {cuenta.nombre} histórico en movimiento {entrada.orden_dia} '
        f'del {entrada.fecha} ({entrada.concepto})')


def test_si_cuenta_tiene_madre_y_recibe_movimiento_incluye_lista_de_dicts_de_ancestro_con_nombre_y_saldo_historico(
        subsubcuenta, entrada):
    context = subsubcuenta.as_template_context(movimiento=entrada)
    assert \
        [x['saldo_gral'] for x in context['ancestros']] == \
        [x.saldo_en_mov(entrada) for x in reversed(subsubcuenta.ancestros())]


def test_si_cuenta_tiene_madre_y_recibe_movimiento_incluye_lista_de_dicts_de_hermana_con_nombre_y_saldo_historico(
        subsubcuenta, entrada, salida, client):
    context = subsubcuenta.as_template_context(movimiento=entrada)
    assert \
        [x['saldo_gral'] for x in context['hermanas']] == \
        [x.saldo_en_mov(entrada) for x in subsubcuenta.hermanas()]
