from django.urls import reverse
from pytest_django import asserts


def test_get_usa_template_titular_confirm_delete(client, titular):
    response = client.get(reverse('tit_elim', args=[titular.sk]))
    asserts.assertTemplateUsed(response, 'diario/titular_confirm_delete.html')


def test_post_redirige_a_home_despues_de_borrar(client, titular):
    response = client.post(reverse('tit_elim', args=[titular.sk]))
    asserts.assertRedirects(response, reverse('home'))


def test_post_elimina_titular(client, titular, mocker):
    mock_delete = mocker.patch('diario.views.Titular.delete')
    client.post(reverse('tit_elim', args=[titular.sk]))
    mock_delete.assert_called_once()
