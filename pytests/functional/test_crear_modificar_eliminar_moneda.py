from django.urls import reverse

from utils.numeros import float_format


def test_crear_moneda(browser, cuenta_con_saldo, cuenta_con_saldo_negativo, cuenta_ajena):
    """ Cuando vamos a la página de moneda nueva y completamos el formulario,
        aparece una moneda nueva entre las monedas del sitio.
    """
    browser.ir_a_pag(reverse("mon_nueva"))
    browser.completar_form(
        nombre="moneda nueva",
        monname="mn",
        cotizacion="15",
    )
    browser.assert_url(reverse('home'))

    # Vemos que la moneda creada aparece entre las monedas de la página de
    # inicio, con su cotización al lado
    links_moneda = browser.esperar_elementos("class_link_moneda")
    nombres_moneda = [x.text.strip() for x in links_moneda]
    assert "moneda nueva" in nombres_moneda
    cot_moneda = browser.esperar_elemento("id_cotizacion_mn")
    assert cot_moneda.text == float_format(15)


def test_modificar_moneda(browser, dolar):
    # Vamos a la página de modificación de la moneda donde cambiamos algunos
    # campos
    browser.ir_a_pag(reverse("mon_mod", args=[dolar.monname]))
    browser.completar_form(
        nombre="dolar canadiense",
        monname="dc"
    )

    # Somos dirigidos a la página principal donde verificamos que el nombre
    # de la moneda cambió de acuerdo a lo que ingresamos
    browser.assert_url(reverse('home'))
    nombre_moneda = browser.esperar_elemento("id_link_mon_dc").text
    assert nombre_moneda == "dolar canadiense"


def test_eliminar_moneda(browser, dolar, euro):
    nombre_moneda = dolar.nombre
    # Verificamos que antes de la eliminación la moneda aparece entre las de
    # la página
    browser.ir_a_pag(reverse('home'))
    links_moneda = browser.esperar_elementos("class_link_moneda")
    nombres_moneda = [x.text.strip() for x in links_moneda]
    assert nombre_moneda in nombres_moneda

    # Vamos a la página de eliminación de la moneda y confirmamos
    browser.ir_a_pag(reverse("mon_elim", args=[dolar.monname]))
    browser.pulsar("id_btn_confirm")

    # Somos dirigidos a la página principal donde verificamos que el nombre
    # de la moneda ya no aparece entre las de la página
    browser.assert_url(reverse("home"))
    links_moneda = browser.esperar_elementos("class_link_moneda")
    nombres_moneda = [x.text.strip() for x in links_moneda]
    assert nombre_moneda not in nombres_moneda



def test_cambiar_cotizacion_moneda(browser):
    pass
