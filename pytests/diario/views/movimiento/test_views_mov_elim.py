from pytest_django import asserts

from diario.models import Movimiento


def test_get_usa_template_movimiento_confirm_delete(client, entrada):
    response = client.get(entrada.get_delete_url())
    asserts.assertTemplateUsed(
        response, 'diario/movimiento_confirm_delete.html')


def test_post_elimina_movimiento(client, entrada):
    cantidad = Movimiento.cantidad()
    client.post(entrada.get_delete_url())
    assert Movimiento.cantidad() == cantidad - 1
