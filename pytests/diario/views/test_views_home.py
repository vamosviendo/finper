import pytest
from django.template.response import TemplateResponse
from django.urls import reverse
from pytest_django import asserts

from utils.iterables import dict_en_lista, listas_de_dicts_iguales
from diario.settings_app import TEMPLATE_HOME
from diario.utils.utils_saldo import saldo_general_historico


@pytest.fixture
def response(client) -> TemplateResponse:
    return client.get(reverse('home'))


def test_usa_template_indicada_en_settings_app(client):
    response = client.get('/')
    asserts.assertTemplateUsed(response, template_name=TEMPLATE_HOME)


def test_pasa_titulares_a_template(titular, otro_titular, response):
    assert titular in response.context.get('titulares')
    assert otro_titular in response.context.get('titulares')


def test_pasa_cuentas_a_template(cuenta, cuenta_ajena, response):
    assert cuenta in response.context.get("cuentas")
    assert cuenta_ajena in response.context.get("cuentas")


def test_pasa_cuentas_ordenadas_por_nombre(client, cuenta, cuenta_2, cuenta_ajena):
    cuenta.nombre = 'J'
    cuenta_2.nombre = 'z'
    cuenta_ajena.nombre = 'a'
    for c in cuenta, cuenta_2, cuenta_ajena:
        c.full_clean()
        c.save()
    response = client.get(reverse('home'))
    assert list(response.context.get("cuentas")) == [cuenta_ajena, cuenta, cuenta_2]


def test_pasa_monedas_a_template(peso, dolar, euro, response):
    for moneda in (peso, dolar, euro):
        assert moneda in response.context.get('monedas')


def test_pasa_dias_a_template(dia_con_movs, dia_anterior_con_movs, dia_posterior_con_movs, dia_tardio_con_movs, response):
    for d in (dia_con_movs, dia_anterior_con_movs, dia_posterior_con_movs, dia_tardio_con_movs):
        assert d in response.context.get('dias')

def test_pasa_dias_ordenados_por_fecha_invertida(
        dia_con_movs, dia_anterior_con_movs, dia_posterior_con_movs, dia_tardio_con_movs, response):
    assert response.context.get('dias')[0] == dia_tardio_con_movs


def test_pasa_solo_los_ultimos_7_dias(mas_de_7_dias, response):
    assert len(response.context.get('dias')) == 7
    assert mas_de_7_dias.first() not in response.context.get('dias')


def test_no_pasa_dias_sin_movimientos(dia, dia_anterior, dia_posterior, entrada, salida_posterior, response):
    assert dia_anterior not in response.context.get('dias')


def test_puede_pasar_movimientos_posteriores(mas_de_7_dias, client):
    response = client.get('/?page=2')
    assert mas_de_7_dias.first() in response.context.get('dias')
    assert mas_de_7_dias.last() not in response.context.get('dias')


def test_pasa_todas_las_cuentas_a_template(cuenta, cuenta_acumulativa, response):
    cuentas = response.context['cuentas']
    sc1, sc2 = cuenta_acumulativa.arbol_de_subcuentas()
    for c in [cuenta, cuenta_acumulativa, sc1, sc2]:
        assert c in cuentas


def test_pasa_saldo_general_a_template(
        cuenta, cuenta_2, entrada, entrada_otra_cuenta, salida, response):
    assert response.context.get('saldo_gral') == cuenta.saldo + cuenta_2.saldo


def test_pasa_titulo_de_saldo_general_a_template(response):
    assert response.context.get('titulo_saldo_gral') is not None
    assert response.context['titulo_saldo_gral'] == "Saldo general"


def test_si_recibe_slug_de_cuenta_pasa_cuenta_como_filtro(
        cuenta, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert response.context['filtro'] == cuenta


def test_si_recibe_slug_de_cuenta_actualiza_context_con_cuenta(
        cuenta, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert response.context['cuenta'] == cuenta


def test_si_recibe_slug_de_cuenta_acumulativa_actualiza_context_con_lista_de_titulares_de_subcuentas(
        cuenta_de_dos_titulares, client):
    response = client.get(reverse('cuenta', args=[cuenta_de_dos_titulares.slug]))
    assert list(response.context['titulares']) == cuenta_de_dos_titulares.titulares


def test_si_recibe_slug_de_cuenta_interactiva_actualiza_context_con_lista_con_nombre_de_titular(
        cuenta, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert list(response.context['titulares']) == [cuenta.titular]


def test_si_recibe_slug_de_cuenta_actualiza_context_con_dias_con_movimientos_de_la_cuenta(
        cuenta, entrada, entrada_anterior, entrada_posterior_otra_cuenta, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert list(response.context['dias']) == [entrada.dia, entrada_anterior.dia]


def test_si_recibe_slug_de_cuenta_pasa_solo_los_ultimos_7_dias_con_movimientos_de_la_cuenta(
        cuenta, mas_de_7_dias, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert len(response.context['dias']) == 7
    assert mas_de_7_dias.first() not in response.context.get('dias')


def test_si_recibe_slug_de_cuenta_pasa_saldo_de_cuenta_como_saldo_general(
        cuenta_con_saldo, entrada, client):
    response = client.get(reverse('cuenta', args=[cuenta_con_saldo.slug]))
    assert response.context['saldo_gral'] == cuenta_con_saldo.saldo


def test_si_recibe_slug_de_cuenta_pasa_titulo_de_saldo_gral_con_cuenta(cuenta, client):
    response = client.get(reverse('cuenta', args=[cuenta.slug]))
    assert response.context['titulo_saldo_gral'] == f"{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion})"


def test_si_recibe_slug_de_cuenta_e_id_de_movimiento_pasa_titulo_de_saldo_historico_con_cuenta_y_movimiento(
        entrada, client):
    cuenta = entrada.cta_entrada
    response = client.get(reverse('cuenta_movimiento', args=[cuenta.slug, entrada.pk]))
    assert (
        response.context['titulo_saldo_gral'] ==
        f'{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion}) en movimiento {entrada.orden_dia} '
        f'del {entrada.fecha} ({entrada.concepto})')


def test_si_recibe_titname_actualiza_context_con_titular(
        titular, cuenta, cuenta_2, entrada, salida, client):
    response = client.get(reverse('titular', args=[titular.titname]))
    assert response.context['titular'] == titular


def test_si_recibe_titname_pasa_titular_como_filtro(titular, client):
    response = client.get(reverse('titular', args=[titular.titname]))
    assert response.context['filtro'] == titular


def test_si_recibe_titname_pasa_titulares_a_template(titular, otro_titular, client):
    response = client.get(reverse('titular', args=[titular.titname]))
    assert \
        list(response.context['titulares']) == [titular, otro_titular]


def test_si_recibe_titname_actualiza_context_con_dias_con_movimientos_del_titular_en_orden_inverso(
        titular, entrada, entrada_anterior,
        entrada_posterior_otra_cuenta, entrada_tardia_cuenta_ajena, client):
    response = client.get(reverse('titular', args=[titular.titname]))
    assert \
        list(response.context['dias']) == \
        [entrada_posterior_otra_cuenta.dia, entrada.dia, entrada_anterior.dia]


def test_si_recibe_titname_pasa_solo_los_ultimos_7_dias_con_movimientos_del_titular(
        titular, mas_de_7_dias, client):
    response = client.get(reverse('titular', args=[titular.titname]))
    assert len(response.context['dias']) == 7
    assert mas_de_7_dias.first() not in response.context.get('dias')


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


def test_si_recibe_id_de_movimiento_pasa_movimiento_a_template(entrada, client):
    response = client.get(reverse('movimiento', args=[entrada.pk]))
    assert response.context['movimiento'] == entrada


def test_si_recibe_id_de_movimiento_pasa_saldo_general_historico_al_momento_del_movimiento_como_saldo_gral(
        entrada, salida, salida_posterior, client):
    response = client.get(reverse('movimiento', args=[salida.pk]))
    assert response.context['saldo_gral'] == saldo_general_historico(salida)


def test_si_recibe_id_de_movimiento_pasa_cuentas_independientes(
        entrada, salida, entrada_otra_cuenta, cuenta_acumulativa, client):
    cuenta = entrada.cta_entrada
    otra_cuenta = entrada_otra_cuenta.cta_entrada
    response = client.get(reverse('movimiento', args=[salida.pk]))
    assert response.context.get('cuentas') is not None
    assert \
        list(response.context["cuentas"]) == \
        [cuenta, otra_cuenta, cuenta_acumulativa] + list(cuenta_acumulativa.subcuentas.all())


def test_si_recibe_id_de_movimiento_pasa_titulares_en_formato_dict(
        entrada, salida, entrada_cuenta_ajena, client):
    titular = entrada.cta_entrada.titular
    otro_titular = entrada_cuenta_ajena.cta_entrada.titular
    response = client.get(reverse('movimiento', args=[salida.pk]))
    assert response.context.get('titulares') is not None
    assert list(response.context['titulares']) == [titular, otro_titular]


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
