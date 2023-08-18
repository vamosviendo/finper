from django.urls import reverse
from selenium.webdriver.common.by import By


def test_agregar_subcuenta(browser, cuenta_acumulativa):
    # Vamos a la página principal, cliqueamos en botón "Edit" de una cuenta
    # acumulativa y luego en el botón "Agregar subcuenta" que aparece en la
    # página de modificación de la cuenta
    browser.ir_a_pag()
    browser.esperar_elemento(f'id_link_cta_mod_{cuenta_acumulativa.slug}').click()
    browser.esperar_elemento('id_btn_agregar').click()

    # En el formulario que aparece, escribimos nombre y slug para la nueva
    # subcuenta a agregar
    browser.completar("id_nombre", "subcuenta 3")
    browser.completar("id_slug", "sc3")
    browser.pulsar()

    # Somos dirigidos a la página de detalle de la cuenta acumulativa
    browser.assert_url(reverse('cuenta', args=[cuenta_acumulativa.slug]))

    # Vemos que la cuenta agregada aparece entre las subcuentas de la
    # cuenta acumulativa.
    divs_cuenta = [
        x.text.strip()
        for x in browser.esperar_elementos('class_link_cuenta')
    ]
    assert "subcuenta 3" in divs_cuenta


def test_agregar_subcuenta_otro_titular(
        browser, cuenta_acumulativa, otro_titular):
    # Vamos a la página de agregar subcuenta de una cuenta acumulativa
    browser.ir_a_pag(
        reverse('cta_agregar_subc', args=[cuenta_acumulativa.slug])
    )

    # Al completar el formulario, agregamos un titular a la subcuenta agregada
    browser.completar("id_nombre", "subcuenta 3")
    browser.completar("id_slug", "sc3")
    browser.completar("id_titular", "Otro Titular")
    browser.pulsar()

    # Vamos a la página de detalles del titular agregado
    browser.ir_a_pag(reverse('tit_detalle', args=[otro_titular.titname]))

    # Vemos que la cuenta agregada aparece entre las cuentas del titular
    divs_cuenta = [
        x.text.strip()
        for x in browser.esperar_elementos('class_link_cuenta')
    ]
    assert "subcuenta 3" in divs_cuenta
