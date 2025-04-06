from django.urls import reverse
from pytest_django import asserts

from diario.models import Cuenta


def test_get_usa_template_cuenta_confirm_delete(client, cuenta):
    response = client.get(reverse('cta_elim', args=[cuenta.sk]))
    asserts.assertTemplateUsed(response, 'diario/cuenta_confirm_delete.html')


def test_post_elimina_cuenta(client, cuenta):
    cantidad = Cuenta.cantidad()
    client.post(reverse('cta_elim', args=[cuenta.sk]))
    assert Cuenta.cantidad() == cantidad - 1


def test_redirige_a_home_despues_de_borrar(client, cuenta):
    response = client.post(reverse('cta_elim', args=[cuenta.sk])
    )
    asserts.assertRedirects(response, reverse('home'))


def test_muestra_mensaje_de_error_si_se_elimina_cuenta_con_saldo(client, cuenta_con_saldo):
    response = client.get(reverse('cta_elim', args=[cuenta_con_saldo.sk]))
    asserts.assertContains(response, 'No se puede eliminar cuenta con saldo')
