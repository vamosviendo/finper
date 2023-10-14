from django.urls import reverse

from diario.models import Cuenta, Titular, Movimiento
from diario.utils import saldo_general_historico
from utils.numeros import float_format


def test_detalle_movimiento(browser, entrada, salida, traspaso, cuenta_acumulativa):
    browser.ir_a_pag()
    links_movimiento = browser.esperar_elementos("class_link_movimiento")

    # Cuando cliqueamos en un movimiento, el movimiento aparece como
    # seleccionado
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" not in movimientos[4].get_attribute("class")
    links_movimiento[4].click()
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movimientos[4].get_attribute("class")

    # Y en el saldo de la página aparece el saldo histórico al momento del
    # movimiento seleccionado
    assert \
        browser.esperar_elemento("id_importe_saldo_gral").text == \
        float_format(saldo_general_historico(salida))

    # Y al lado de cada cuenta aparece el saldo de la cuenta al momento del
    # movimiento seleccionado
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_saldo_cuenta")]
    for index, cta in enumerate(Cuenta.todes()):
        assert saldos_historicos[index] == float_format(cta.saldo_en_mov(salida))

    # Y al lado de cada titular aparece el capital del titular al momento del
    # movimiento seleccionado
    capitales_historicos = [
        x.text for x in browser.esperar_elementos("class_capital_titular")]
    for index, titular in enumerate(Titular.todes()):
        assert capitales_historicos[index] == float_format(titular.capital_historico(salida))


def test_detalle_movimiento_en_cuenta_acumulativa(browser, titular, otro_titular, fecha):
    # Creamos una cuenta
    browser.ir_a_pag(reverse('cta_nueva'))
    browser.completar_form(
        nombre="cuenta",
        slug="c",
    )
    cuenta = Cuenta.tomar(slug='c')

    # La dividimos en dos subcuentas con saldo cero
    browser.ir_a_pag(reverse('cta_div', args=cuenta.slug))
    browser.completar_form(
        fecha=fecha,
        form_0_nombre='primera subcuenta',
        form_0_slug='psc',
        form_0_saldo='0',
        form_0_titular=titular.nombre,
        form_1_nombre='segunda subcuenta',
        form_1_slug='ssc',
        form_1_titular=otro_titular.nombre,
    )
    sc1 = Cuenta.tomar(slug='psc')
    sc2 = Cuenta.tomar(slug='ssc')

    # Cargamos un saldo a la primera subcuenta por medio de un movimiento
    browser.ir_a_pag(reverse('mov_nuevo'))
    browser.completar_form(
        fecha=f'{fecha.year}-{fecha.month:02d}-{fecha.day:02d}',
        concepto='Saldo al inicio sc1',
        importe='110',
        cta_entrada=sc1.nombre
    )

    # Id para la segunda subcuenta
    browser.ir_a_pag(reverse('mov_nuevo'))
    browser.completar_form(
        fecha=f'{fecha.year}-{fecha.month:02d}-{fecha.day:02d}',
        concepto='Saldo al inicio sc2',
        importe='88',
        cta_entrada=sc2.nombre
    )
    mov1 = Movimiento.tomar(concepto='Saldo al inicio sc1')
    mov2 = Movimiento.tomar(concepto='Saldo al inicio sc2')

    link_mov_1 = browser.esperar_elemento(f'id_link_mov_{mov1.identidad}')
    link_mov_1.click()
    saldo_sc1 = browser.esperar_elemento('id_saldo_cta_psc')
    saldo_sc2 = browser.esperar_elemento('id_saldo_cta_ssc')
    saldo_c = browser.esperar_elemento('id_saldo_cta_c')
    assert saldo_sc1.text == '110,00'
    assert saldo_sc2.text == '0,00'
    assert saldo_c.text == '110,00'

    link_mov_2 = browser.esperar_elemento(f'id_link_mov_{mov2.identidad}')
    link_mov_2.click()
    saldo_sc1 = browser.esperar_elemento('id_saldo_cta_psc')
    saldo_sc2 = browser.esperar_elemento('id_saldo_cta_ssc')
    saldo_c = browser.esperar_elemento('id_saldo_cta_c')
    assert saldo_sc1.text == '110,00'
    assert saldo_sc2.text == '88,00'
    assert saldo_c.text == '198,00'
