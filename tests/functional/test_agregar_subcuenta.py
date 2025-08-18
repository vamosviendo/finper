from django.urls import reverse


def test_agregar_subcuenta(browser, cuenta_acumulativa, fecha_posterior):
    # Vamos a la página "Agregar subcuenta"
    browser.ir_a_pag(reverse('cta_agregar_subc', args=[cuenta_acumulativa.sk]))

    # En el formulario que aparece, escribimos nombre y sk para la nueva
    # subcuenta a agregar
    browser.completar("id_nombre", "subcuenta 3")
    browser.completar("id_sk", "sc3")
    browser.completar("id_fecha", fecha_posterior)
    browser.pulsar()

    # Somos dirigidos a la página de detalle de la cuenta acumulativa
    browser.assert_url(cuenta_acumulativa.get_absolute_url())

    # Vemos que la cuenta agregada aparece entre las subcuentas de la
    # cuenta acumulativa.
    divs_cuenta = [
        x.text.strip()
        for x in browser.esperar_elementos('class_link_cuenta')
    ]
    assert "subcuenta 3" in divs_cuenta

    # Vamos a la página de detalle de la cuenta, donde comprobamos
    # que su fecha de creación coincide con la fecha que ingresamos en
    # el formulario
    browser.ir_a_pag(reverse('cuenta', args=['sc3']))
    titulo_pag = browser.esperar_elemento("id_titulo_saldo_gral").text.strip()
    assert fecha_posterior.strftime("%Y-%m-%d") in titulo_pag


def test_agregar_subcuenta_otro_titular(
        browser, cuenta_acumulativa, otro_titular):
    # Vamos a la página de agregar subcuenta de una cuenta acumulativa
    browser.ir_a_pag(
        reverse('cta_agregar_subc', args=[cuenta_acumulativa.sk])
    )

    # Al completar el formulario, agregamos un titular a la subcuenta agregada
    browser.completar("id_nombre", "subcuenta 3")
    browser.completar("id_sk", "sc3")
    browser.completar("id_titular", "Otro Titular")
    browser.pulsar()

    # Vamos a la página de detalles del titular agregado
    browser.ir_a_pag(reverse('titular', args=[otro_titular.sk]))

    # Vemos que la cuenta agregada aparece entre las cuentas del titular
    divs_cuenta = [
        x.text.strip()
        for x in browser.esperar_elementos('class_link_cuenta')
    ]
    assert "subcuenta 3" in divs_cuenta
