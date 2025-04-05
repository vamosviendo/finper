from django.urls import reverse
from pytest_django import asserts


def test_get_usa_template_moneda_confirm_delete(client, dolar):
    response = client.get(reverse('mon_elim', args=[dolar.sk]))
    asserts.assertTemplateUsed(response, 'diario/moneda_confirm_delete.html')


def test_post_redirige_a_home_despues_de_borrar(client, dolar):
    response = client.post(reverse('mon_elim', args=[dolar.sk]))
    asserts.assertRedirects(response, reverse('home'))


def test_post_elimina_moneda(client, dolar, mocker):
    mock_delete = mocker.patch('diario.views.Moneda.delete')
    client.post(reverse('mon_elim', args=[dolar.sk]))
    mock_delete.assert_called_once()
