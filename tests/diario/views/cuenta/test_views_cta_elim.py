from pytest_django import asserts

from diario.models import Cuenta, Movimiento


def test_get_usa_template_cuenta_confirm_delete(client, cuenta):
    response = client.get(cuenta.get_delete_url())
    asserts.assertTemplateUsed(response, 'diario/cuenta_confirm_delete.html')


def test_post_elimina_cuenta(client, cuenta):
    cantidad = Cuenta.cantidad()
    client.post(cuenta.get_delete_url())
    assert Cuenta.cantidad() == cantidad - 1


def test_post_muestra_mensaje_de_error_si_se_elimina_cuenta_con_movimientos(client, cuenta_con_saldo):
    Movimiento.crear("puesta en cero", importe=cuenta_con_saldo.saldo(), cta_salida=cuenta_con_saldo)
    response = client.post(cuenta_con_saldo.get_delete_url())
    asserts.assertContains(
        response,
        "No se puede eliminar una cuenta con movimientos existentes ni un titular con cuentas con movimientos existentes. "
        "Si es una cuenta, intente desactivarla"
    )

def test_post_muestra_mensaje_de_error_si_se_elimina_cuenta_con_saldo(client, cuenta_con_saldo):
    response = client.post(cuenta_con_saldo.get_delete_url())
    asserts.assertContains(
        response,
        'No se puede eliminar cuenta con saldo distinto de cero o titular con capital distinto de cero'
    )
