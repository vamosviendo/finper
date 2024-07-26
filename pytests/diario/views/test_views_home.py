import pytest
from django.urls import reverse
from pytest_django import asserts

from diario.settings_app import TEMPLATE_HOME
from diario.utils.utils_saldo import saldo_general_historico


@pytest.fixture
def response(client):
    return client.get(reverse('home'))


def test_usa_template_indicada_en_settings_app(client):
    response = client.get('/')
    asserts.assertTemplateUsed(response, template_name=TEMPLATE_HOME)


def test_pasa_titulares_a_template(titular, otro_titular, response):
    assert titular.as_view_context() in response.context.get('titulares')
    assert otro_titular.as_view_context() in response.context.get('titulares')


def test_pasa_cuentas_a_template(cuenta, cuenta_ajena, response):
    assert cuenta.as_view_context() in response.context.get('cuentas')
    assert cuenta_ajena.as_view_context() in response.context.get('cuentas')


def test_pasa_cuentas_ordenadas_por_nombre(client, cuenta, cuenta_2, cuenta_ajena):
    cuenta.nombre = 'J'
    cuenta_2.nombre = 'z'
    cuenta_ajena.nombre = 'a'
    for c in cuenta, cuenta_2, cuenta_ajena:
        c.full_clean()
        c.save()
    response = client.get(reverse('home'))

    assert \
        list(response.context.get('cuentas')) == \
        [x.as_view_context() for x in [cuenta_ajena, cuenta, cuenta_2]]


def test_pasa_monedas_a_template(peso, dolar, euro, response):
    for moneda in (peso, dolar, euro):
        assert moneda.as_view_context() in response.context.get('monedas')


def test_pasa_dias_a_template_como_dict(dia_con_movs, dia_anterior_con_movs, dia_posterior_con_movs, dia_tardio_con_movs, response):
    for d in (dia_con_movs, dia_anterior_con_movs, dia_posterior_con_movs, dia_tardio_con_movs):
        assert d.as_view_context() in response.context.get('dias')

def test_pasa_dias_ordenados_por_fecha_invertida(
        dia_con_movs, dia_anterior_con_movs, dia_posterior_con_movs, dia_tardio_con_movs, response):
    assert response.context.get('dias')[0] == dia_tardio_con_movs.as_view_context()


def test_pasa_solo_7_dias(mas_de_7_dias, response):
    assert len(response.context.get('dias')) == 7
    assert mas_de_7_dias.first() not in response.context.get('dias')


def test_no_pasa_dias_sin_movimientos(dia, dia_anterior, dia_posterior, entrada, salida_posterior, response):
    assert dia_anterior not in response.context.get('dias')


def test_puede_pasar_movimientos_posteriores(mas_de_7_dias, client):
    response = client.get('/?page=2')
    assert mas_de_7_dias.first().as_view_context() in response.context.get('dias')
    assert mas_de_7_dias.last().as_view_context() not in response.context.get('dias')

def test_pasa_movimientos_a_template(entrada, salida, traspaso, response):
    for mov in (entrada, salida, traspaso):
        assert mov.as_view_context() in response.context.get('movimientos')


def test_pasa_solo_cuentas_independientes_a_template(cuenta, cuenta_acumulativa, response):
    cuentas = response.context['cuentas']
    sc1, sc2 = cuenta_acumulativa.arbol_de_subcuentas()

    assert cuenta.as_view_context() in cuentas
    assert cuenta_acumulativa.as_view_context() in cuentas
    assert sc1.as_view_context() not in cuentas
    assert sc2.as_view_context() not in cuentas


def test_pasa_saldo_general_a_template(
        cuenta, cuenta_2, entrada, entrada_otra_cuenta, salida, response):
    assert response.context.get('saldo_gral') == cuenta.saldo + cuenta_2.saldo


def test_pasa_titulo_de_saldo_general_a_template(response):
    assert response.context.get('titulo_saldo_gral') is not None
    assert response.context['titulo_saldo_gral'] == "Saldo general"


def test_si_recibe_slug_de_cuenta_actualiza_context_con_datos_de_cuenta(
        cuenta, cuenta_acumulativa, mocker, client):
    mock_avci = mocker.patch('diario.models.CuentaInteractiva.as_view_context', autospec=True)
    mock_avca = mocker.patch('diario.models.CuentaAcumulativa.as_view_context', autospec=True)
    mock_avci.return_value = {
        'nombre': cuenta.nombre,
        'saldo': cuenta.saldo,
        'saldos': {'p': cuenta.saldo},
        'titulares': [cuenta.titular.as_view_context()],
        'cuentas': [],
        'movimientos': [m.as_view_context() for m in cuenta.movs()],
        'ctaname': cuenta.slug,
        'fecha_alta': cuenta.fecha_creacion,
    }
    mock_avca.return_value = {
        'nombre': cuenta_acumulativa.nombre,
        'saldo': cuenta_acumulativa.saldo,
        'titulares': [t.as_view_context() for t in cuenta_acumulativa.titulares],
        'cuentas': [c.as_view_context() for c in cuenta_acumulativa.subcuentas.all()],
        'movimientos': [m.as_view_context() for m in cuenta.movs()],
        'ctaname': cuenta.slug,
        'fecha_alta': cuenta.fecha_creacion
    }
    mock_avca.reset_mock()
    mock_avci.reset_mock()
    response = client.get(reverse('cuenta', args=[cuenta.slug]))

    mock_avci.assert_called_once_with(cuenta, None, True)
    for key, value in cuenta.as_view_context().items():
        assert response.context.get(key) is not None
        assert response.context[key] == value

    response = client.get(reverse('cuenta', args=[cuenta_acumulativa.slug]))
    mock_avca.assert_called_once_with(cuenta_acumulativa, None, True)
    for key, value in cuenta_acumulativa.as_view_context().items():
        assert response.context.get(key) is not None
        assert response.context[key] == value


def test_si_recibe_slug_de_cuenta_pasa_saldo_de_cuenta_como_saldo_general(
        cuenta_con_saldo, entrada, client):
    response = client.get(reverse('cuenta', args=[cuenta_con_saldo.slug]))
    assert response.context['saldo_gral'] == cuenta_con_saldo.saldo


def test_si_recibe_slug_de_cuenta_pasa_titulo_de_saldo_gral_con_cuenta(cuenta, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert response.context['titulo_saldo_gral'] == f"{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion})"


def test_si_recibe_slug_de_cuenta_pasa_solo_dias_con_movimientos_de_la_cuenta(
        cuenta, dia, dia_posterior, dia_tardio,
        entrada, salida, entrada_posterior_otra_cuenta, entrada_tardia,
        client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert response.context["dias"] == [dia.as_view_context() for dia in [dia_tardio, dia]]


def test_si_recibe_slug_de_cuenta_e_id_de_movimiento_actualiza_context_con_datos_historicos_de_cuenta_al_momento_del_movimiento(
        cuenta, entrada, mocker, client):
    mock_avc = mocker.patch('diario.models.CuentaInteractiva.as_view_context', autospec=True)
    mock_avc.return_value = {
        'nombre': cuenta.nombre,
        'saldo': cuenta.saldo_en_mov(entrada),
        'titulares': [cuenta.titular],
        'cuentas': [],
        'movimientos': cuenta.movs(),
        'movimiento': entrada,
        'slug': cuenta.slug,
        'fecha_alta': cuenta.fecha_creacion,
    }
    response = client.get(reverse('cuenta_movimiento', args=[cuenta.slug, entrada.pk]))
    mock_avc.assert_called_once_with(cuenta, entrada, True)
    for key, value in cuenta.as_view_context().items():
        assert response.context.get(key) is not None
        assert response.context[key] == value, f"key: {key}"


def test_si_recibe_slug_de_cuenta_e_id_de_movimiento_pasa_titulo_de_saldo_historico_con_cuenta_y_movimiento(
        entrada, client):
    cuenta = entrada.cta_entrada
    response = client.get(reverse('cuenta_movimiento', args=[cuenta.slug, entrada.pk]))
    assert (
        response.context['titulo_saldo_gral'] ==
        f'{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion}) en movimiento {entrada.orden_dia} '
        f'del {entrada.fecha} ({entrada.concepto})')


def test_si_recibe_titname_actualiza_context_con_datos_de_titular(
        titular, cuenta, cuenta_2, entrada, salida, mocker, client):
    mock_avc = mocker.patch('diario.models.Titular.as_view_context', autospec=True)
    mock_avc.return_value = {
            'nombre': titular.nombre,
            'titname': titular.titname,
            'capital': titular.capital,
            'titulo_saldo_gral':
                f'Capital de {titular.nombre}',
            'cuentas': [x.as_view_context() for x in (cuenta, cuenta_2)],
            'movimientos': [entrada, salida],
        }
    response = client.get(reverse('titular', args=[titular.titname]))
    mock_avc.assert_any_call(titular, None, True)
    for key, value in mock_avc.return_value.items():
        assert response.context[key] == value


def test_si_recibe_pk_de_movimiento_actualiza_context_con_datos_de_movimiento(
        entrada, salida, mocker, client):
    mock_avc = mocker.patch('diario.models.Movimiento.as_view_context', autospec=True)
    mock_avc.return_value = {
        'pk': entrada.pk,
        'saldo_gral': saldo_general_historico(entrada),
        'concepto': entrada.concepto,
        'detalle': entrada.detalle,
        'fecha': entrada.fecha,
        'importe': entrada.importe,
        'cta_entrada': entrada.cta_entrada,
        'es_automatico': entrada.es_automatico,
    }
    response = client.get(reverse('movimiento', args=[entrada.pk]))
    mock_avc.assert_any_call(entrada)
    for key, value in mock_avc.return_value.items():
        assert response.context[key] == value


def test_si_recibe_titname_y_pk_de_movimiento_actualiza_context_con_datos_de_titular_al_momento_del_movimiento(
        titular, cuenta, cuenta_2, entrada, salida, mocker, client):
    mock_atc = mocker.patch('diario.models.Titular.as_view_context', autospec=True)
    mock_atc.return_value = {
            'nombre': titular.nombre,
            'titname': titular.titname,
            'capital': titular.capital,
            'cuentas': [x.as_view_context() for x in (cuenta, cuenta_2)],
            'movimientos': [entrada, salida],
            'movimiento': entrada,
        }
    response = client.get(
        reverse(
            'titular_movimiento',
            args=[titular.titname, entrada.pk]
        )
    )
    mock_atc.assert_any_call(titular, entrada, True)
    for key, value in mock_atc.return_value.items():
        assert response.context[key] == value


def test_si_recibe_titname_pasa_titulares_a_template(titular, otro_titular, client):
    response = client.get(reverse('titular', args=[titular.titname]))
    assert \
        list(response.context['titulares']) == \
        [x.as_view_context() for x in (titular, otro_titular)]


def test_si_recibe_titname_e_id_de_movimiento_pasa_saldo_historico_de_titulares_al_momento_del_movimiento(
        titular, otro_titular, entrada, salida, entrada_cuenta_ajena, client):
    response = client.get(reverse('titular_movimiento', args=[titular.titname, entrada.pk]))
    assert \
        [x['capital'] for x in response.context['titulares']] == \
        [x.capital_historico(entrada) for x in (titular, otro_titular)]


def test_si_recibe_titname_e_id_de_movimiento_pasa_titulo_de_saldo_gral_con_titular_y_movimiento(
        entrada, client):
    titular = entrada.cta_entrada.titular
    response = client.get(
        reverse(
            'titular_movimiento',
            args=[titular.titname, entrada.pk])
    )
    assert response.context.get('titulo_saldo_gral') is not None
    assert \
        response.context['titulo_saldo_gral'] == \
        f"Capital de {titular.nombre} en movimiento {entrada.orden_dia} " \
        f"del {entrada.fecha} ({entrada.concepto})"


def test_si_recibe_id_de_movimiento_pasa_todos_los_movimientos_en_formato_dict_a_template(
        entrada, salida, traspaso, client):
    response = client.get(reverse('movimiento', args=[entrada.pk]))
    assert \
        response.context['movimientos'] == \
        [x.as_view_context() for x in [entrada, salida, traspaso]]


def test_si_recibe_id_de_movimiento_pasa_movimiento_en_formato_dict_a_template(entrada, client):
    response = client.get(reverse('movimiento', args=[entrada.pk]))
    assert response.context['movimiento'] == entrada.as_view_context()


def test_si_recibe_id_de_movimiento_pasa_saldo_general_historico_al_momento_del_movimiento_como_saldo_gral(
        entrada, salida, salida_posterior, client):
    response = client.get(reverse('movimiento', args=[salida.pk]))
    assert response.context['saldo_gral'] == saldo_general_historico(salida)


def test_si_recibe_id_de_movimiento_pasa_cuentas_independientes_en_formato_dict(
        entrada, salida, entrada_otra_cuenta, cuenta_acumulativa, client):
    cuenta = entrada.cta_entrada
    otra_cuenta = entrada_otra_cuenta.cta_entrada
    response = client.get(reverse('movimiento', args=[salida.pk]))
    assert response.context.get('cuentas') is not None
    assert \
        list(response.context['cuentas']) == [
            x.as_view_context(salida)
            for x in (cuenta, otra_cuenta, cuenta_acumulativa)
        ]


def test_si_recibe_id_de_movimiento_pasa_titulares_en_formato_dict(
        entrada, salida, entrada_cuenta_ajena, client):
    titular = entrada.cta_entrada.titular
    otro_titular = entrada_cuenta_ajena.cta_entrada.titular
    response = client.get(reverse('movimiento', args=[salida.pk]))
    assert response.context.get('titulares') is not None
    assert list(response.context['titulares']) == [
        x.as_view_context(salida) for x in (titular, otro_titular)]


def test_si_recibe_id_de_movimiento_pasa_titulo_de_saldo_gral_con_movimiento(
        entrada, client):
    response = client.get(reverse('movimiento', args=[entrada.pk]))
    assert (
        response.context['titulo_saldo_gral'] ==
        f'Saldo general en movimiento {entrada.orden_dia} '
        f'del {entrada.fecha} ({entrada.concepto})')


def test_considera_solo_cuentas_independientes_para_calcular_saldo_gral(
        cuenta, cuenta_2, entrada, entrada_otra_cuenta, salida, client):
    cuenta_2.dividir_entre(
        {'nombre': 'subcuenta 2.1', 'slug': 'sc21', 'saldo': 200},
        {'nombre': 'subcuenta 2.2', 'slug': 'sc22'},
    )
    cuenta_2 = cuenta_2.tomar_del_slug()
    response = client.get(reverse('home'))

    assert response.context['saldo_gral'] == cuenta.saldo + cuenta_2.saldo


def test_si_no_hay_movimientos_pasa_0_a_saldo_general(response):
    assert response.context['saldo_gral'] == 0
