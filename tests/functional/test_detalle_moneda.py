def test_detalle_moneda(browser, dolar):
    # Dada una moneda, vamos a la página principal y cliqueamos en la moneda
    browser.ir_a_pag()
    browser.cliquear_en_moneda(dolar)

    # Somos dirigidos a la página de detalle de la moneda cliqueada
    browser.assert_url(dolar.get_absolute_url())
