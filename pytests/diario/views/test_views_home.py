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


def test_si_recibe_slug_de_cuenta_pasa_cuenta_a_template(cuenta, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert response.context.get('cuenta') is not None
    assert response.context['cuenta'] == cuenta


def test_si_recibe_slug_de_cuenta_interactiva_pasa_lista_con_titular_de_cuenta_como_titulares(
        cuenta, otro_titular, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert list(response.context['titulares']) == [cuenta.titular]


def test_si_recibe_slug_de_cuenta_acumulativa_pasa_lista_de_titulares_de_la_cuenta(
        cuenta_de_dos_titulares, titular_gordo, client):
    response = client.get(reverse('cuenta', args=[cuenta_de_dos_titulares.slug]))
    assert list(response.context['titulares']) == cuenta_de_dos_titulares.titulares


def test_si_recibe_slug_de_cuenta_pasa_saldo_de_cuenta_como_saldo_general(
        cuenta_con_saldo, entrada, client):
    response = client.get(reverse('cuenta', args=[cuenta_con_saldo.slug]))
    assert response.context['saldo_gral'] == cuenta_con_saldo.saldo


def test_si_recibe_slug_de_cuenta_pasa_movimientos_de_la_cuenta_recibida(
        cuenta, entrada, salida, entrada_otra_cuenta, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert list(response.context['movimientos']) == list(cuenta.movs())


def test_si_recibe_slug_de_cuenta_acumulativa_pasa_subcuentas_de_la_cuenta_recibida(
        cuenta_acumulativa, cuenta, client):
    response = client.get(reverse('cuenta', args=[cuenta_acumulativa.slug]))
    assert list(response.context['subcuentas']) == list(cuenta_acumulativa.subcuentas.all())


def test_si_recibe_slug_de_cuenta_interactiva_pasa_lista_vacia_de_subcuentas(
        cuenta, cuenta_2, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert len(response.context['subcuentas']) == 0


def test_si_recibe_titname_pasa_titular_a_template(
        titular, client):
    response = client.get(reverse('titular', args=[titular.titname]))
    assert response.context.get('titular') is not None
    assert response.context['titular'] == titular


def test_si_recibe_titname_pasa_saldo_a_template(entrada, entrada_cuenta_ajena, client):
    titular = entrada.cta_entrada.titular
    response = client.get(reverse('titular', args=[titular.titname]))
    assert response.context['saldo_gral'] == titular.capital


def test_si_recibe_titname_pasa_titulares_a_template(titular, otro_titular, client):
    response = client.get(reverse('titular', args=[titular.titname]))
    assert list(response.context['titulares']) == [titular, otro_titular]


def test_si_recibe_titname_pasa_cuentas_del_titular_a_template(
        cuenta_2, cuenta, cuenta_ajena, client):
    titular = cuenta.titular
    response = client.get(reverse('titular', args=[titular.titname]))
    assert set(response.context['subcuentas']) == {cuenta, cuenta_2}


def test_si_recibe_titname_pasa_cuentas_del_titular_ordenadas_por_nombre(
        cuenta_2, cuenta, cuenta_ajena, client):
    titular = cuenta.titular
    response = client.get(reverse('titular', args=[titular.titname]))
    assert list(response.context['subcuentas']) == [cuenta, cuenta_2]


def test_si_recibe_titname_pasa_movimientos_del_titular_a_template(
        entrada, salida, traspaso, entrada_cuenta_ajena, client):
    titular = entrada.cta_entrada.titular
    response = client.get(reverse('titular', args=[titular.titname]))
    assert list(response.context['movimientos']) == list(titular.movs())


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
