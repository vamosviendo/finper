from django.urls import reverse


def test_desactivar_cuenta(browser, cuenta, cuenta_2, cuenta_3):
    """ Cuando vamos a la página de desactivar cuent y cliqueamos en confirmar,
        la cuenta deja de aparecer entre las cuentas de la lista en la página
        principal, y empieza a aparecer en la lista de cuentas de la página
        de cuentas inactivas.
    """
    # Comprobamos que al inicio la cuenta está entre las cuentas de la página principal,
    # y no aparece en la página de cuentas inactivas
    browser.ir_a_pag()
    assert browser.cuenta_esta(cuenta_2)
    browser.ir_a_pag(reverse("ctas_inactivas"))
    assert not browser.cuenta_esta(cuenta_2)

    # Desactivamos la cuenta
    browser.ir_a_pag(cuenta_2.get_toggle_url())
    browser.pulsar("id_btn_confirm")

    # La cuenta ya no aparece en la página principal
    browser.assert_url(reverse("home"))
    assert not browser.cuenta_esta(cuenta_2)

    # y aparece en la página de cuentas inactivas
    browser.ir_a_pag(reverse("ctas_inactivas"))
    assert browser.cuenta_esta(cuenta_2)


def test_desactivar_cuenta_con_saldo_distinto_de_cero(browser, cuenta_con_saldo):
    """ Si intentamos modificar una cuenta con saldo distinto de cero,
        al pulsar el botón de confirmación aparecerá un mensaje de error
        y la cuenta no se desactivará.
    """
    browser.ir_a_pag(cuenta_con_saldo.get_toggle_url())
    browser.pulsar("id_btn_confirm")
    msj = browser.encontrar_elemento("id_div_errores")
    assert msj.text == "No se puede desactivar cuenta con saldo distinto de cero"
    browser.ir_a_pag()
    assert browser.cuenta_esta(cuenta_con_saldo)


def test_activar_cuenta(browser, cuenta, cuenta_inactiva, cuenta_3):
    # Comprobamos que al inicio la cuenta está entre las cuentas inactivas,
    # y no aparece en la página principal
    browser.ir_a_pag()
    assert not browser.cuenta_esta(cuenta_inactiva)
    browser.ir_a_pag(reverse("ctas_inactivas"))
    assert browser.cuenta_esta(cuenta_inactiva)

    # Activamos la cuenta
    browser.ir_a_pag(cuenta_inactiva.get_toggle_url())
    browser.pulsar("id_btn_confirm")

    # La cuenta aparece en la página principal
    browser.assert_url(reverse("home"))
    assert browser.cuenta_esta(cuenta_inactiva)

    # Y ya no aparece en la página de cuentas inactivas
    browser.ir_a_pag(reverse("ctas_inactivas"))
    assert not browser.cuenta_esta(cuenta_inactiva)
