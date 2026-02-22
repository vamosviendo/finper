from django.urls import reverse


def test_pasa_solamente_cuentas_inactivas_a_template(client, cuenta, cuenta_2, cuenta_inactiva):
    response = client.get(reverse("ctas_inactivas"))
    cuentas = response.context.get("cuentas")
    assert cuenta_inactiva in cuentas
    assert cuenta not in cuentas
    assert cuenta_2 not in cuentas


def test_si_pasa_subcuenta_inactiva_pasa_cuenta_madre_antes_de_la_subcuenta(client, cuenta_acumulativa_saldo_0):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    sc3 = cuenta_acumulativa_saldo_0.agregar_subcuenta("subcuenta 3", "sc3", sc1.titular)
    for sc in sc1, sc3:
        sc.activa = False
        sc.clean_save()

    response = client.get(reverse("ctas_inactivas"))
    assert response.context.get("cuentas") == [cuenta_acumulativa_saldo_0, sc1, sc3]
