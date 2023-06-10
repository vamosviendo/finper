import pytest
from django.urls import reverse
from pytest_django import asserts

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
    assert cuenta in response.context.get('subcuentas')
    assert cuenta_ajena in response.context.get('subcuentas')


def test_pasa_cuentas_ordenadas_por_nombre(client, cuenta, cuenta_2, cuenta_ajena):
    cuenta.nombre = 'J'
    cuenta.save()
    cuenta_2.nombre = 'z'
    cuenta_2.save()
    cuenta_ajena.nombre = 'a'
    cuenta_ajena.save()
    response = client.get(reverse('home'))

    assert \
        list(response.context.get('subcuentas')) == \
        [cuenta_ajena, cuenta, cuenta_2]


def test_pasa_movimientos_a_template(entrada, salida, traspaso, response):
    for mov in (entrada, salida, traspaso):
        assert mov in response.context.get('movimientos')


def test_pasa_solo_cuentas_independientes_a_template(cuenta, cuenta_acumulativa, response):
    cuentas = response.context['subcuentas']
    sc1, sc2 = cuenta_acumulativa.arbol_de_subcuentas()

    assert cuenta in cuentas
    assert cuenta_acumulativa in cuentas
    assert sc1 not in cuentas
    assert sc2 not in cuentas


def test_pasa_saldo_general_a_template(
        cuenta, cuenta_2, entrada, entrada_otra_cuenta, salida, response):
    assert response.context.get('saldo_gral') == cuenta.saldo + cuenta_2.saldo


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
