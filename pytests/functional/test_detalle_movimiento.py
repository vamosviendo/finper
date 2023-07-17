from diario.utils import saldo_general_historico
from utils.numeros import float_format


def test_detalle_movimiento(browser, entrada, salida, traspaso):
    cuenta = entrada.cta_entrada
    cuenta_2 = traspaso.cta_salida
    browser.ir_a_pag()
    links_movimiento = browser.esperar_elementos("class_link_movimiento")

    # Cuando cliqueamos en un movimiento, el movimiento aparece como
    # seleccionado
    assert "mov_selected" not in links_movimiento[0].get_attribute("class")
    links_movimiento[0].click()
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movimientos[0].get_attribute("class")

    # Y en el saldo de la página aparece el saldo histórico al momento del
    # movimiento seleccionado
    assert \
        browser.esperar_elemento("id_importe_saldo_gral").text == \
        float_format(saldo_general_historico(traspaso))

    # Y al lado de cada cuenta aparece el saldo de la cuenta al momento del
    # movimiento seleccionado
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_saldo_cuenta")]
    assert saldos_historicos[0] == float_format(cuenta.saldo)
    assert saldos_historicos[1] == float_format(cuenta_2.saldo)