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
    # inicio
    links_moneda = browser.esperar_elementos("class_link_moneda")
    nombres_moneda = [x.text.strip() for x in links_moneda]
    assert "moneda nueva" in nombres_moneda

    # Vemos que al lado de la moneda aparece la cotización de la misma
    cot_moneda = browser.esperar_elemento("id_cotizacion_mn")
    assert cot_moneda.text == float_format(15)

    # Vemos que en la sección de saldos aparecen los saldos generales en distintas
    # monedas, así como una columna para el saldo total expresado en cada una de
    # las monedas existentes.
    saldo_general = sum(c.saldo for c in Cuenta.filtro(cta_madre=None))
    saldo_en_moneda_nueva = browser.esperar_elemento("id_saldo_gral_mn")
    assert saldo_en_moneda_nueva.text == '0,00'
    saldo_expresado_en_moneda_nueva = browser.esperar_elemento("id_saldo_gral_expresado_en_mn")
    assert saldo_expresado_en_moneda_nueva == float_format(saldo_general / 15)

    # Vemos que al lado de cada cuenta aparece una columna con su saldo expresado
    # en la nueva moneda, en una tipografía más clara que la de su moneda original
    for cuenta in Cuenta.todes():
        saldo_mon_nueva = browser.esperar_elemento(f"id_saldo_cta_{cuenta.slug}_en_mn")
        assert saldo_mon_nueva.text == float_format(cuenta.saldo / 15)

    # Vemos que al lado de cada titular aparece una columna para su capital
    # en la nueva moneda, así como una columna para el capital total expresado
    # en cada una de las monedas existentes
    for titular in Titular.todes():
        capital_en_mon_nueva = browser.esperar_elemento(f"id_capital_{titular.titname}_en_mn")
        assert capital_en_mon_nueva.text == "0.00"
        capital_expresado_en_mon_nueva = titular.esperar_elemento(f"id_capital_{titular.titname}_expresado_en_mn")
        assert capital_expresado_en_mon_nueva.text == float_format(titular.capital / 15)

    # Vemos que en la sección de movimientos aparece una columna para el importe
    # de movimientos hechos en la nueva moneda
    browser.esperar_elemento("id_th_importe_mn")
    for movimiento in Movimiento.todes():
        importe_en_mon_nueva = browser.esperar_elemento("class_td_importe_mn")
        assert importe_en_mon_nueva.text == '0.00'


def test_modificar_moneda(browser):
    pass


def test_cambiar_cotizacion_moneda(browser):
    pass