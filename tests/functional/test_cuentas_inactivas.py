from django.urls import reverse
from selenium.webdriver.common.by import By


def test_permite_activar_cuentas_inactivas(browser, cuenta_inactiva, cuenta):
    # En la página de cuentas inactivas, al lado de cada cuenta hay una opción "A"
    # Si cliqueamos en esa opción y pulsamos el botón de confirmación, la cuenta se activa.
    browser.ir_a_pag(reverse("ctas_inactivas"))
    browser.encontrar_elemento("A", By.LINK_TEXT).click()
    browser.pulsar("id_btn_confirm")
    browser.assert_url(reverse("ctas_inactivas"))

    # La cuenta desaparece de la página de cuentas inactivas
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta', fail=False)]
    assert cuenta_inactiva.nombre not in nombres_cuenta

    # y aparece entre las cuentas de la página principal
    browser.ir_a_pag()
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta', fail=False)]
    assert cuenta_inactiva.nombre in nombres_cuenta

