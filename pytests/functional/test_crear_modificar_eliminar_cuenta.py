import pytest
from django.urls import reverse


def test_crear_cuenta(browser, titular):
    """ Cuando vamos a la página de cuenta nueva y completamos el formulario,
        aparece una cuenta nueva entre las cuentas del sitio. """
    browser.ir_a_pag(reverse("cta_nueva"))
    browser.completar_form(
        nombre="cuenta nueva",
        slug="cn",
        titular="Titular"
    )
    browser.assert_url(reverse("home"))

    # Vemos que la cuenta creada aparece entre las cuentas de la página de
    # inicio
    links_cuenta = browser.esperar_elementos("class_link_cuenta")
    nombres_cuenta = [x.text.strip() for x in links_cuenta]
    assert "cuenta nueva" in nombres_cuenta


@pytest.mark.xfail
def test_crear_cuenta_con_saldo(browser, titular):
    ...


def test_modificar_cuenta(browser, cuenta):
    """ Cuando vamos a la página de modificar cuenta y completamos el
        formulario, la cuenta se modifica"""
    browser.ir_a_pag(reverse('cta_mod', args=[cuenta.slug]))
    browser.completar_form(
        nombre="cuenta con nombre modificado",
        slug="ccnm",
    )
    browser.assert_url(reverse("home"))
    nombre_cuenta = browser.esperar_elemento("id_link_cta_ccnm").text.strip()
    assert nombre_cuenta == "cuenta con nombre modificado"


def test_eliminar_cuenta(browser, cuenta, cuenta_2):
    """ Cuando vamos a la página de eliminar cuenta y cliqueamos en confirmar,
        la cuenta es eliminada"""
    nombre_cuenta = cuenta.nombre
    browser.ir_a_pag(reverse('cta_elim', args=[cuenta.slug]))
    browser.pulsar('id_btn_confirm')
    browser.assert_url(reverse('home'))
    nombres_cuenta = [x.text.strip() for x in browser.esperar_elementos('class_link_cuenta')]
    assert nombre_cuenta not in nombres_cuenta
