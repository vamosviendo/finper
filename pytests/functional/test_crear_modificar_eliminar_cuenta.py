import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By


@pytest.fixture(autouse=True)
def mock_titular_principal(mocker, titular):
    return mocker.patch('diario.forms.TITULAR_PRINCIPAL', titular.sk)


def test_crear_cuenta(browser, titular, fecha):
    """ Cuando vamos a la página de cuenta nueva y completamos el formulario,
        aparece una cuenta nueva entre las cuentas del sitio. """
    browser.ir_a_pag(reverse("cta_nueva"))
    browser.completar_form(
        nombre="cuenta nueva",
        sk="cn",
        titular=titular.nombre,
        fecha_creacion=fecha,
    )
    browser.assert_url(reverse("home"))

    # Vemos que la cuenta creada aparece entre las cuentas de la página de
    # inicio
    links_cuenta = browser.esperar_elementos("class_link_cuenta")
    nombres_cuenta = [x.text.strip() for x in links_cuenta]
    assert "cuenta nueva" in nombres_cuenta


def test_crear_cuenta_en_otra_moneda(browser, titular, fecha, dolar):
    browser.ir_a_pag(reverse("cta_nueva"))
    browser.completar_form(
        nombre="cuenta en dólares",
        sk="cd",
        titular=titular.nombre,
        fecha_creacion=fecha,
        moneda=dolar.nombre,
    )
    # Vemos que la cuenta creada tiene resaltado como saldo principal el saldo
    # en dólares
    saldo_cuenta = browser.esperar_elemento("id_row_cta_cd").esperar_elemento("mon_cuenta", By.CLASS_NAME)
    assert saldo_cuenta.get_attribute("id") == f"id_saldo_cta_cd_{dolar.sk}"


def test_modificar_cuenta(browser, cuenta_ajena, dolar, fecha_anterior):
    """ Cuando vamos a la página de modificar cuenta y completamos el
        formulario, la cuenta se modifica"""
    browser.ir_a_pag(reverse('cta_mod', args=[cuenta_ajena.sk]))
    # En todos los campos del formulario aparece el valor del campo correspondiente de la cuenta:
    browser.controlar_modelform(instance=cuenta_ajena)

    browser.completar_form(
        nombre="cuenta con nombre modificado",
        sk="ccnm",
    )
    browser.assert_url(reverse("home"))
    nombre_cuenta = browser.esperar_elemento("id_link_cta_ccnm").text.strip()
    assert nombre_cuenta == "cuenta con nombre modificado"


def test_eliminar_cuenta(browser, cuenta, cuenta_2):
    """ Cuando vamos a la página de eliminar cuenta y cliqueamos en confirmar,
        la cuenta es eliminada"""
    nombre_cuenta = cuenta.nombre
    browser.ir_a_pag(reverse('cta_elim', args=[cuenta.sk]))
    browser.pulsar('id_btn_confirm')
    browser.assert_url(reverse('home'))
    nombres_cuenta = [x.text.strip() for x in browser.esperar_elementos('class_link_cuenta')]
    assert nombre_cuenta not in nombres_cuenta
