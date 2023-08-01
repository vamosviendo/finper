from diario.models import Cuenta, Titular
from diario.utils import saldo_general_historico
from utils.numeros import float_format


def test_detalle_movimiento(browser, entrada, salida, traspaso, cuenta_acumulativa):
    cuenta = entrada.cta_entrada
    cuenta_2 = traspaso.cta_salida
    subc1, subc2 = cuenta_acumulativa.subcuentas.all()
    browser.ir_a_pag()
    links_movimiento = browser.esperar_elementos("class_link_movimiento")

    # Cuando cliqueamos en un movimiento, el movimiento aparece como
    # seleccionado
    assert "mov_selected" not in links_movimiento[4].get_attribute("class")
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
