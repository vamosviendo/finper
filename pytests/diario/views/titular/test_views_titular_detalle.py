from unittest.mock import PropertyMock

from django.urls import reverse
from pytest_django import asserts


def test_usa_template_home(client, titular):
    response = client.get(
        reverse('tit_detalle', args=[titular.titname]))
    asserts.assertTemplateUsed(response, 'diario/home.html')


def test_pasa_titulares_a_template(client, titular, otro_titular):
    response = client.get(
        reverse('tit_detalle', args=[titular.titname]))
    assert titular in response.context.get('titulares')
    assert otro_titular in response.context.get('titulares')


def test_pasa_titular_al_template(client, titular):
    response = client.get(
        reverse('tit_detalle', args=[titular.titname]))
    assert response.context['titular'] == titular


def test_pasa_cuentas_del_titular_al_template(
        client, titular, cuenta, cuenta_2, cuenta_ajena):
    response = client.get(
        reverse('tit_detalle', args=[titular.titname]))

    assert list(response.context['subcuentas']) == [cuenta, cuenta_2]


def test_pasa_cuentas_ordenadas_por_slug(client, titular, cuenta_2, cuenta_3):

    response = client.get(
        reverse('tit_detalle', args=[titular.titname]))

    assert list(response.context['subcuentas']) == [cuenta_2, cuenta_3]


def test_pasa_capital_del_titular_al_template(client, mocker, titular):
    mock_capital = mocker.patch(
        'diario.views.Titular.capital',
        new_callable=PropertyMock
    )
    mock_capital.return_value = 252

    response = client.get(reverse('tit_detalle', args=[titular.titname]))

    assert response.context['saldo_gral'] == 252


def test_pasa_movimientos_relacionados_con_cuentas_del_titular_al_template(
        client, titular, entrada, entrada_otra_cuenta, entrada_cuenta_ajena):
    response = client.get(reverse('tit_detalle', args=[titular.titname]))
    assert 'movimientos' in response.context.keys()
    assert \
        list(response.context['movimientos']) == [entrada, entrada_otra_cuenta]

