from django.urls import reverse


def test_crear_titular(browser):
    """ Cuando vamos a la página de titular nuevo y completamos el formulario,
        aparece un titular nuevo entre los titulares del sitio. """
    browser.ir_a_pag(reverse("tit_nuevo"))
    browser.completar_form(
        nombre="titular nuevo",
        titname="tn",
    )
    browser.assert_url(reverse("home"))

    # Vemos que la cuenta creada aparece entre las cuentas de la página de
    # inicio
    nombre_titular = browser.esperar_elemento('id_link_tit_tn').text.strip()
    assert nombre_titular == "titular nuevo"


def test_modificar_titular(browser, titular):
    """ Cuando vamos a la página de modificar titular y completamos el
        formulario, vemos el titular modificado en la página principal """
    browser.ir_a_pag(reverse('tit_mod', args=[titular.titname]))
    browser.completar_form(
        nombre="titular con nombre modificado",
        titname="tcnm",
    )
    browser.assert_url(reverse('home'))

    nombre_titular = browser.esperar_elemento('id_link_tit_tcnm').text.strip()
    assert nombre_titular == "titular con nombre modificado"


def test_eliminar_titular(browser, titular, otro_titular):
    """ Cuando vamos a la página de eliminar titular y cliqueamos en confirmar,
        el titular es eliminado"""
    nombre_titular = titular.nombre
    browser.ir_a_pag(reverse('tit_elim', args=[titular.titname]))
    browser.pulsar('id_btn_confirm')
    browser.assert_url(reverse('home'))
    nombres_titular = [x.text.strip() for x in browser.esperar_elementos('class_link_titular')]
    assert nombre_titular not in nombres_titular
