import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django import asserts

from diario.models import Movimiento


def test_get_usa_template_movimiento_confirm_delete(client, entrada):
    response = client.get(reverse('mov_elim', args=[entrada.pk]))
    asserts.assertTemplateUsed(
        response, 'diario/movimiento_confirm_delete.html')


def test_post_elimina_movimiento(client, entrada):
    cantidad = Movimiento.cantidad()
    client.post(reverse('mov_elim', args=[entrada.pk]))
    assert Movimiento.cantidad() == cantidad - 1


def test_post_redirige_a_url_recibida_en_querystring(client, cuenta, entrada):
    response = client.post(reverse("mov_elim", args=[entrada.pk]) + f"?next=/diario/c/{cuenta.sk}/")
    asserts.assertRedirects(response, f"/diario/c/{cuenta.sk}/")


def test_post_redirige_a_home_si_no_recibe_url_en_querystring(client, cuenta, entrada):
    response = client.post(reverse('mov_elim', args=[entrada.pk]))
    asserts.assertRedirects(response, reverse('home'))
