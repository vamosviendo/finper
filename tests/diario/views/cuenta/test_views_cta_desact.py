from pytest_django import asserts


def test_get_usa_template_cuenta_confirm_desact(client, cuenta):
    response = client.get(cuenta.get_toggle_url())
    asserts.assertTemplateUsed(response, 'diario/cta_confirm_desact.html')


def test_get_pasa_cuenta_como_objeto(client, cuenta):
    response = client.get(cuenta.get_toggle_url())
    assert response.context.get("object").sk == cuenta.sk


def test_post_desactiva_cuenta_activa(client, cuenta):
    client.post(cuenta.get_toggle_url())
    cuenta.refresh_from_db()
    assert cuenta.activa is False


def test_post_activa_cuenta_inactiva(client, cuenta_inactiva):
    client.post(cuenta_inactiva.get_toggle_url())
    cuenta_inactiva.refresh_from_db()
    assert cuenta_inactiva.activa is True


def test_post_pasa_mensaje_de_error_si_se_intenta_desactivar_cuenta_con_saldo_distinto_de_cero(
        client, cuenta_con_saldo):
    response = client.post(cuenta_con_saldo.get_toggle_url())
    assert response.context.get("error") == ["No se puede desactivar cuenta con saldo distinto de cero"]
