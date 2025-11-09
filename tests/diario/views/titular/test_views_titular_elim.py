from django.urls import reverse
from pytest_django import asserts

from diario.models import Movimiento


def test_get_usa_template_titular_confirm_delete(client, titular):
    response = client.get(titular.get_delete_url())
    asserts.assertTemplateUsed(response, 'diario/titular_confirm_delete.html')


def test_post_redirige_a_home_despues_de_borrar(client, titular):
    response = client.post(titular.get_delete_url())
    asserts.assertRedirects(response, reverse('home'))


def test_post_elimina_titular(client, titular, mocker):
    mock_delete = mocker.patch('diario.views.Titular.delete')
    client.post(titular.get_delete_url())
    mock_delete.assert_called_once()


def test_post_muestra_mensaje_de_error_si_se_elimina_titular_con_cuenta_con_saldo(client, titular, cuenta_con_saldo):
    response = client.post(titular.get_delete_url())
    asserts.assertContains(
        response,
        'No se puede eliminar cuenta con saldo distinto de cero o titular con capital distinto de cero'
    )


def test_post_muestra_mensaje_de_error_si_se_elimina_titular_con_cuenta_con_movimientos(client, titular, cuenta_con_saldo):
    Movimiento.crear("puesta en cero", importe=cuenta_con_saldo.saldo(), cta_salida=cuenta_con_saldo)
    response = client.post(titular.get_delete_url())
    asserts.assertContains(
        response,
        "No se puede eliminar una cuenta con movimientos existentes ni un titular con cuentas con movimientos existentes. "
        "Si es una cuenta, intente desactivarla"
    )

