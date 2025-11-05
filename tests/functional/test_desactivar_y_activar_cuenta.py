from django.urls import reverse


def test_desactivar_cuenta(browser, cuenta, cuenta_2, cuenta_3):
    """ Cuando vamos a la página de desactivar cuent y cliqueamos en confirmar,
        la cuenta deja de aparecer entre las cuentas de la lista en la página
        principal, y empieza a aparecer en la lista de cuentas de la página
        de cuentas inactivas.
    """
    nombre_cuenta = cuenta_2.nombre
    # Comprobamos que al inicio la cuenta está entre las cuentas de la página principal,
    # y no aparece en la página de cuentas inactivas
    browser.ir_a_pag()
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos("class_link_cuenta")]
    assert nombre_cuenta in nombres_cuenta
    browser.ir_a_pag(reverse("ctas_inactivas"))
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos("class_link_cuenta", fail=False)]
    assert nombre_cuenta not in nombres_cuenta

    # Desactivamos la cuenta
    browser.ir_a_pag(cuenta_2.get_toggle_url())
    browser.pulsar("id_btn_confirm")

    # La cuenta ya no aparece en la página principal
    browser.assert_url(reverse("home"))
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos("class_link_cuenta")]
    assert nombre_cuenta not in nombres_cuenta

    # y aparece en la página de cuentas inactivas
    browser.ir_a_pag(reverse("ctas_inactivas"))
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta')]
    assert nombre_cuenta in nombres_cuenta


def test_activar_cuenta(browser, cuenta, cuenta_inactiva, cuenta_3):
    nombre_cta_inactiva = cuenta_inactiva.nombre

    # Comprobamos que al inicio la cuenta está entre las cuentas inactivas,
    # y no aparece en la página principal
    browser.ir_a_pag()
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta')]
    assert nombre_cta_inactiva not in nombres_cuenta
    browser.ir_a_pag(reverse("ctas_inactivas"))
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta')]
    assert nombre_cta_inactiva in nombres_cuenta

    # Activamos la cuenta
    browser.ir_a_pag(cuenta_inactiva.get_toggle_url())
    browser.pulsar("id_btn_confirm")

    # La cuenta aparece en la página principal
    browser.assert_url(reverse("home"))
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta')]
    assert nombre_cta_inactiva in nombres_cuenta

    # Y ya no aparece en la página de cuentas inactivas
    browser.ir_a_pag(reverse("ctas_inactivas"))
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta', fail=False)]
    assert nombre_cta_inactiva not in nombres_cuenta
