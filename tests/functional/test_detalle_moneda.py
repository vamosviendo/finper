from selenium.webdriver.common.by import By

from utils.numeros import float_format


def test_detalle_moneda(browser, dolar, cotizacion_dolar, cotizacion_posterior_dolar, cotizacion_tardia_dolar):
    # Dada una moneda con varias cotizaciones, vamos a la página principal y cliqueamos en la moneda
    browser.ir_a_pag()
    browser.cliquear_en_moneda(dolar)

    # Somos dirigidos a la página de detalle de la moneda cliqueada
    browser.assert_url(dolar.get_absolute_url())

    # Vemos el nombre de la moneda encabezando la página
    titulo = browser.esperar_elemento("id_nombre")
    assert titulo.text == f"Moneda: {dolar.nombre}"

    # Y vemos que al lado del nombre de la moneda aparece la última cotización de la misma
    cotizacion_compra = browser.esperar_elemento("id_cotizacion_compra")
    cotizacion_venta = browser.esperar_elemento("id_cotizacion_venta")
    cotizacion_moneda = dolar.cotizaciones.last()
    assert cotizacion_compra.text == float_format(cotizacion_moneda.importe_compra)
    assert cotizacion_venta.text == float_format(cotizacion_moneda.importe_venta)

    # Y vemos que debajo del nombre aparece una lista con las cotizaciones anteriores
    cotizaciones_historicas = browser.esperar_elementos("class_cotizacion_historica")
    cotizaciones_bd = dolar.cotizaciones.reverse()
    for index, cot in enumerate(cotizaciones_bd):
        cot_mostrada = cotizaciones_historicas[index]
        assert cot_mostrada.esperar_elemento("class_cot_hist_fecha", By.CLASS_NAME).text == cot.fecha
        assert \
            cot_mostrada.esperar_elemento("class_cot_hist_compra", By.CLASS_NAME).text == \
            float_format(cot.importe_compra)
        assert \
            cot_mostrada.esperar_elemento("class_cot_hist_venta", By.CLASS_NAME).text == \
            float_format(cot.importe_venta)

    # Y vemos que al final de la lista aparece un link que, al cliquear en él, nos lleva a la página principal

    # Si vamos a la página de detalle de moneda desde una página que no sea la principal, al cliquear en el link
    # regresamos a esa página.
