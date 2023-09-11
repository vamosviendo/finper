import pytest
from django.urls import reverse
from pytest_django import asserts

from diario.utils import saldo_general_historico


@pytest.fixture
def response(client):
    return client.get(reverse('home'))


def test_usa_template_home(client):
    response = client.get('/')
    asserts.assertTemplateUsed(response, 'diario/home.html')


def test_pasa_titulares_a_template(titular, otro_titular, response):
    assert titular in response.context.get('titulares')
    assert otro_titular in response.context.get('titulares')


def test_pasa_cuentas_a_template(cuenta, cuenta_ajena, response):
    assert cuenta.as_view_context() in response.context.get('cuentas')
    assert cuenta_ajena.as_view_context() in response.context.get('cuentas')


def test_pasa_cuentas_ordenadas_por_nombre(client, cuenta, cuenta_2, cuenta_ajena):
    cuenta.nombre = 'J'
    cuenta.save()
    cuenta_2.nombre = 'z'
    cuenta_2.save()
    cuenta_ajena.nombre = 'a'
    cuenta_ajena.save()
    response = client.get(reverse('home'))

    assert \
        list(response.context.get('cuentas')) == \
        [x.as_view_context() for x in [cuenta_ajena, cuenta, cuenta_2]]


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
        'titulares': [cuenta.titular],
        'cuentas': [],
        'movimientos': cuenta.movs(),
        'slug': cuenta.slug,
    }
    mock_avca.return_value = {
        'nombre': cuenta_acumulativa.nombre,
        'saldo': cuenta_acumulativa.saldo,
        'titulares': cuenta_acumulativa.titulares,
        'cuentas': cuenta_acumulativa.subcuentas.all(),
        'movimientos': cuenta.movs(),
        'slug': cuenta.slug,
    }
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
    assert response.context['titulo_saldo_gral'] == f"Saldo de {cuenta.nombre}"


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
        f'Saldo de {cuenta.nombre} histórico en movimiento {entrada.orden_dia} '
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
        'str_cuentas': entrada.str_cuentas(),
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


class TestsIntegrativos:

    def test_si_recibe_slug_de_cuenta_interactiva_pasa_lista_con_titular_de_cuenta_como_titulares(
            self, cuenta, otro_titular, client):
        response = client.get(reverse('cuenta', args=[cuenta.slug]))
        assert response.context['titulares'] == [cuenta.titular.as_view_context()]

    def test_si_recibe_slug_de_cuenta_acumulativa_pasa_lista_de_titulares_de_la_cuenta(
            self, cuenta_de_dos_titulares, titular_gordo, client):
        response = client.get(reverse('cuenta', args=[cuenta_de_dos_titulares.slug]))
        assert response.context['titulares'] == [
            x.as_view_context() for x in cuenta_de_dos_titulares.titulares]

    def test_si_recibe_slug_de_cuenta_pasa_movimientos_de_la_cuenta_recibida_en_formato_dict(
            self, cuenta, entrada, salida, entrada_otra_cuenta, client):
        response = client.get(reverse('cuenta', args=[cuenta.slug]))
        assert \
            response.context['movimientos'] == \
            [x.as_view_context() for x in cuenta.movs()]

    def test_si_recibe_slug_de_cuenta_acumulativa_pasa_subcuentas_de_la_cuenta_recibida_sin_ancestros_ni_hermanas(
            self, cuenta_acumulativa, cuenta, client):
        response = client.get(reverse('cuenta', args=[cuenta_acumulativa.slug]))
        assert \
            response.context['cuentas'] == [
                x.as_view_context()
                for x in cuenta_acumulativa.subcuentas.all()
            ]

    def test_si_recibe_slug_de_cuenta_interactiva_pasa_lista_vacia_de_subcuentas(
            self, cuenta, cuenta_2, client):
        response = client.get(reverse('cuenta', args=[cuenta.slug]))
        assert len(response.context['cuentas']) == 0

    def test_si_recibe_slug_de_subcuenta_pasa_lista_de_dicts_de_ancestro_con_nombre_y_saldo(
            self, subsubcuenta, client):
        response = client.get(reverse('cuenta', args=[subsubcuenta.slug]))
        assert response.context.get('ancestros') is not None
        assert \
            [x['nombre'] for x in response.context['ancestros']] == \
            [x.nombre for x in reversed(subsubcuenta.ancestros())]
        assert \
            [x['saldo'] for x in response.context['ancestros']] == \
            [x.saldo for x in reversed(subsubcuenta.ancestros())]

    def test_si_recibe_slug_de_subcuenta_y_pk_de_movimiento_pasa_lista_de_dicts_de_ancestro_con_nombre_y_saldo_historico(
            self, subsubcuenta, entrada, client):
        response = client.get(reverse('cuenta_movimiento', args=[subsubcuenta.slug, entrada.pk]))
        assert \
            [x['saldo'] for x in response.context['ancestros']] == \
            [x.saldo_en_mov(entrada) for x in reversed(subsubcuenta.ancestros())]

    def test_si_recibe_slug_de_subcuenta_pasa_lista_de_dicts_de_hermana_con_nombre_y_saldo(
            self, subsubcuenta, client):
        madre = subsubcuenta.cta_madre
        madre.agregar_subcuenta('subsubcuenta 3', 'ssc3', subsubcuenta.titular)
        response = client.get(reverse('cuenta', args=[subsubcuenta.slug]))
        assert response.context.get('hermanas') is not None
        assert \
            [(x['nombre'], x['saldo']) for x in response.context['hermanas']] == \
            [(x.nombre, x.saldo) for x in subsubcuenta.hermanas()]

    def test_si_recibe_slug_de_cuenta_e_id_de_movimiento_pasa_movimiento_seleccionado(
            self, entrada, salida, client):
        cuenta = entrada.cta_entrada
        response = client.get(reverse('cuenta_movimiento', args=[cuenta.slug, salida.pk]))
        assert response.context.get('movimiento') is not None
        assert response.context['movimiento'] == salida.as_view_context()

    def test_si_recibe_slug_de_cuenta_e_id_de_movimiento_pasa_saldo_historico_de_cuenta_en_movimiento_como_saldo_gral(
            self, entrada, salida, salida_posterior, client):
        cuenta = entrada.cta_entrada
        response = client.get(reverse('cuenta_movimiento', args=[cuenta.slug, salida.pk]))
        assert response.context.get('saldo_gral') is not None
        assert response.context['saldo_gral'] == cuenta.saldo_en_mov(salida)

    def test_si_recibe_slug_de_subcuenta_y_pk_de_movimiento_pasa_lista_de_dicts_de_hermana_con_nombre_y_saldo_historico(
            self, subsubcuenta, entrada, salida, client):
        response = client.get(reverse('cuenta_movimiento', args=[subsubcuenta.slug, entrada.pk]))
        assert \
            [x['saldo'] for x in response.context['hermanas']] == \
            [x.saldo_en_mov(entrada) for x in subsubcuenta.hermanas()]

    def test_si_recibe_titname_e_id_de_movimiento_pasa_solo_movimientos_de_cuentas_del_titular(
            self, entrada, salida, entrada_cuenta_ajena, client):
        titular = entrada.cta_entrada.titular
        otro_titular = entrada_cuenta_ajena.cta_entrada.titular
        response = client.get(
            reverse(
                'titular_movimiento',
                args=[titular.titname, salida.pk]
            )
        )
        assert response.context.get('movimientos') is not None
        assert \
            response.context['movimientos'] == \
            [x.as_view_context() for x in titular.movs()]

    def test_si_recibe_titname_e_id_de_movimiento_pasa_movimiento_seleccionado_en_formato_dict(
            self, entrada, salida, client):
        titular = entrada.cta_entrada.titular
        response = client.get(
            reverse(
                'titular_movimiento',
                args=[titular.titname, salida.pk]
            )
        )
        assert response.context.get('movimiento') is not None
        assert response.context['movimiento'] == salida.as_view_context()

    def test_si_recibe_titname_e_id_de_movimiento_pasa_capital_historico_de_titular_en_movimiento_como_saldo_gral(
            self, entrada, salida, entrada_otra_cuenta, client):
        titular = entrada.cta_entrada.titular
        response = client.get(
            reverse(
                'titular_movimiento',
                args=[titular.titname, salida.pk])
        )
        assert response.context.get('saldo_gral') is not None
        assert response.context['saldo_gral'] == titular.capital_historico(salida)

    def test_si_recibe_titname_pasa_saldo_a_template(self, entrada, entrada_cuenta_ajena, client):
        titular = entrada.cta_entrada.titular
        response = client.get(reverse('titular', args=[titular.titname]))
        assert response.context['saldo_gral'] == titular.capital

    def test_si_recibe_titname_pasa_titulo_de_saldo_con_titular_a_template(self, titular, client):
        response = client.get(reverse('titular', args=[titular.titname]))
        assert response.context['titulo_saldo_gral'] == f"Capital de {titular.nombre}"

    def test_si_recibe_titname_pasa_cuentas_del_titular_a_template(
            self, cuenta_2, cuenta, cuenta_ajena, client):
        titular = cuenta.titular
        response = client.get(reverse('titular', args=[titular.titname]))
        for c in response.context['cuentas']:
            assert c in [cuenta.as_view_context(), cuenta_2.as_view_context()]

    def test_si_recibe_titname_pasa_cuentas_del_titular_ordenadas_por_nombre(
            self, cuenta_2, cuenta, cuenta_ajena, client):
        titular = cuenta.titular
        response = client.get(reverse('titular', args=[titular.titname]))
        assert \
            list(response.context['cuentas']) == \
            [x.as_view_context() for x in (cuenta, cuenta_2)]

    def test_si_recibe_titname_pasa_movimientos_del_titular_a_template_en_formato_dict(
            self, entrada, salida, traspaso, entrada_cuenta_ajena, client):
        titular = entrada.cta_entrada.titular
        response = client.get(reverse('titular', args=[titular.titname]))
        assert \
            list(response.context['movimientos']) == \
            [x.as_view_context() for x in titular.movs()]


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
        f"Capital de {titular.nombre} histórico en movimiento {entrada.orden_dia} " \
        f"del {entrada.fecha} ({entrada.concepto})"


def test_si_recibe_id_de_movimiento_pasa_todos_los_movimientos_en_formato_dict_a_template(
        entrada, salida, traspaso, client):
    response = client.get(reverse('movimiento', args=[entrada.pk]))
    assert \
        list(response.context['movimientos']) == \
        [x.as_view_context() for x in [entrada, salida, traspaso]]


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
            f'Saldo general histórico en movimiento {entrada.orden_dia} '
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
