from django.urls import reverse

from diario.models import Cuenta, Titular, Movimiento
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


def test_modificar_moneda(browser):
    pass


def test_cambiar_cotizacion_moneda(browser):
    pass