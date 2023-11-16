import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django import asserts

from diario.models import Movimiento
from utils.helpers_tests import dividir_en_dos_subcuentas


@pytest.fixture
def cambio_concepto(client, entrada: Movimiento) -> HttpResponse:
    return client.post(
        reverse('mov_mod', args=[entrada.pk]),
        {
            'fecha': entrada.fecha,
            'concepto': 'Concepto nuevo',
            'importe': entrada.importe,
            'cta_entrada': entrada.cta_entrada.pk,
            'moneda': entrada.cta_entrada.moneda.pk,
        }
    )


def test_usa_template_mov_form(client, entrada):
    response = client.get(reverse('mov_mod', args=[entrada.pk]))
    asserts.assertTemplateUsed(response, 'diario/mov_form.html')


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_mov_tiene_cuenta_acumulativa_en_campo_de_cuenta_la_muestra(
        client, sentido, request):
    mov = request.getfixturevalue(sentido)
    cuenta = dividir_en_dos_subcuentas(getattr(mov, f'cta_{sentido}'))
    response = client.get(reverse('mov_mod', args=[mov.pk]))
    assert cuenta in response.context['form'].fields[f'cta_{sentido}'].queryset


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_cuenta_es_acumulativa_campo_esta_deshabilitado(client, sentido, request):
    mov = request.getfixturevalue(sentido)
    dividir_en_dos_subcuentas(getattr(mov, f'cta_{sentido}'))
    response = client.get(reverse('mov_mod', args=[mov.pk]))
    assert response.context['form'].fields[f'cta_{sentido}'].disabled


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_cuenta_es_interactiva_no_muestra_cuentas_acumulativas_entre_las_opciones(
        client, sentido, cuenta_acumulativa, request):
    mov = request.getfixturevalue(sentido)

    response = client.get(reverse('mov_mod', args=[mov.pk]))
    assert \
        cuenta_acumulativa not in \
        response.context['form'].fields[f'cta_{sentido}'].queryset


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_no_tiene_cta_entrada_no_muestra_cuentas_acumulativas_entre_las_opciones(
        client, sentido, cuenta_acumulativa, request):
    mov = request.getfixturevalue(sentido)
    contrasentido = 'salida' if sentido == 'entrada' else 'entrada'

    response = client.get(reverse('mov_mod', args=[mov.pk]))
    assert \
        cuenta_acumulativa not in \
        response.context['form'].fields[f'cta_{contrasentido}'].queryset


def test_post_guarda_cambios_en_el_mov(entrada, cambio_concepto):
    entrada.refresh_from_db()
    assert entrada.concepto == 'Concepto nuevo'


def test_post_redirige_a_home(entrada, cambio_concepto):
    asserts.assertRedirects(cambio_concepto, reverse('home'))


def test_si_no_se_modifica_importe_no_cambia_saldo_cuentas(entrada, request):
    cuenta = entrada.cta_entrada
    saldo = cuenta.saldo

    request.getfixturevalue('cambio_concepto')

    cuenta.refresh_from_db()
    assert cuenta.saldo == saldo


def test_permite_modificar_fecha_de_movimiento_con_cuenta_acumulativa(
        client, entrada, fecha_posterior, fecha_tardia):
    dividir_en_dos_subcuentas(entrada.cta_entrada, fecha=fecha_tardia)

    client.post(
        reverse('mov_mod', args=[entrada.pk]),
        {
            'fecha': fecha_posterior,
            'concepto': entrada.concepto,
            'importe': entrada.importe,
            'moneda': entrada.cta_entrada.moneda.pk,
        }
    )
    entrada.refresh_from_db()
    assert entrada.fecha == fecha_posterior


def test_si_se_selecciona_esgratis_en_movimiento_entre_titulares_desaparece_contramovimiento(
        client, credito):
    id_contramov = credito.id_contramov

    client.post(
        reverse('mov_mod', args=[credito.pk]),
        {
            'fecha': credito.fecha,
            'concepto': credito.concepto,
            'importe': credito.importe,
            'cta_entrada': credito.cta_entrada.pk,
            'cta_salida': credito.cta_salida.pk,
            'moneda': credito.cta_entrada.moneda.pk,
            'esgratis': True,
        }
    )
    assert Movimiento.filtro(id=id_contramov).count() == 0
