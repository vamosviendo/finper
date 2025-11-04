from django.urls import reverse


def test_pasa_solamente_cuentas_inactivas_a_template(client, cuenta, cuenta_2, cuenta_inactiva):
    response = client.get(reverse("ctas_inactivas"))
    cuentas = response.context.get("cuentas")
    assert cuenta_inactiva in cuentas
    assert cuenta not in cuentas
    assert cuenta_2 not in cuentas
