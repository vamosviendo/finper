import pytest
from django.urls import reverse


# TODO: Agregar comentarios

def test_ir_a_crear_cuenta(browser):
    """ Cuando cliqueamos en el botón "cuenta nueva de la página principal,
        somos dirigidos a la página correspondiente"""
    browser.ir_a_pag()
    browser.esperar_elemento("id_btn_cta_nueva").click()
    browser.assert_url(reverse("cta_nueva"))


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
    slugs_cuenta = [x.text.strip() for x in links_cuenta]
    nombres_cuenta = [x.get_attribute("title") for x in links_cuenta]
    assert "CN" in slugs_cuenta
    assert "cuenta nueva" in nombres_cuenta


@pytest.mark.xfail
def test_crear_cuenta_con_saldo(browser, titular):
    ...
