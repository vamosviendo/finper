import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django import asserts

from diario.models import Movimiento


@pytest.fixture
def response(client) -> HttpResponse:
    return client.get(reverse('mov_nuevo'))


@pytest.fixture
def response_post(client, fecha, importe, cuenta) -> HttpResponse:
    return client.post(
        reverse('mov_nuevo'),
        data={
            'fecha': fecha,
            'concepto': 'mov nuevo',
            'importe': importe,
            'cta_entrada': cuenta.id,
        }
    )


def test_usa_template_mov_form(cuenta, response):
    asserts.assertTemplateUsed(response, 'diario/mov_form.html')


def test_si_no_hay_cuentas_redirige_a_crear_cuenta(response):
    asserts.assertRedirects(response, reverse('cta_nueva'))


def test_no_muestra_cuentas_acumulativas_entre_las_opciones(
        cuenta, cuenta_acumulativa, response):

    opciones_ce = response.context['form'].fields['cta_entrada'].queryset
    opciones_cs = response.context['form'].fields['cta_salida'].queryset

    assert cuenta in opciones_ce
    assert cuenta_acumulativa not in opciones_ce
    assert cuenta in opciones_cs
    assert cuenta_acumulativa not in opciones_cs


def test_post_redirige_a_home(response_post):
    asserts.assertRedirects(response_post, reverse('home'))


def test_post_guarda_movimiento_nuevo(cuenta, fecha, importe, request):
    cantidad = Movimiento.cantidad()
    request.getfixturevalue('response_post')
    assert Movimiento.cantidad() == cantidad + 1
    mov_nuevo = Movimiento.ultime()
    assert mov_nuevo.fecha == fecha
    assert mov_nuevo.concepto == 'mov nuevo'
    assert mov_nuevo.importe == importe
    assert mov_nuevo.cta_entrada.id == cuenta.id


def test_no_guarda_movimientos_no_validos(client, fecha, importe):
    cantidad = Movimiento.cantidad()
    client.post(
        reverse('mov_nuevo'),
        data={
            'fecha': fecha,
            'concepto': 'entrada de efectivo',
            'importe': importe,
        }
    )
    assert Movimiento.cantidad() == cantidad


def test_movimiento_entre_titulares_llama_a_metodo_registrar_credito(
        client, titular, otro_titular, cuenta, cuenta_ajena, fecha, importe, mocker):
    mock_gestionar_transferencia = mocker.patch(
        'diario.views.Movimiento._gestionar_transferencia',
        autospec=True,
    )
    client.post(
        reverse('mov_nuevo'),
        data={
            'fecha': fecha,
            'concepto': 'movimiento entre titulares',
            'importe': importe,
            'cta_entrada': cuenta.id,
            'cta_salida': cuenta_ajena.id
        }
    )
    mov = Movimiento.ultime()
    mock_gestionar_transferencia.assert_called_once_with(mov)
