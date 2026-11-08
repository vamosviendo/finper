from urllib.parse import urlparse

from selenium.webdriver.common.by import By

from utils.numeros import float_format


def test_detalle_moneda(browser, dolar, cotizacion_dolar, cotizacion_posterior_dolar, cotizacion_tardia_dolar):
    # Dada una moneda con varias cotizaciones, vamos a la página principal y cliqueamos en la moneda
    browser.ir_a_pag()
    browser.cliquear_en_moneda(dolar)

    # Somos dirigidos a la página de detalle de la moneda cliqueada
    browser.assert_url(dolar.get_absolute_url())

    # El nombre de la moneda aparece en el título de la página
    assert browser.title == f"Finper - Moneda: {dolar.nombre}"

    # Y encabeza la página
    titulo = browser.encontrar_elemento("id_nombre")
    assert titulo.text == f"Moneda: {dolar.nombre}"

    # Al lado del nombre de la moneda aparece la última cotización de la misma
    cotizacion_fecha = browser.encontrar_elemento("id_cotizacion_fecha")
    cotizacion_compra = browser.encontrar_elemento("id_cotizacion_compra")
    cotizacion_venta = browser.encontrar_elemento("id_cotizacion_venta")
    cotizacion_moneda = dolar.cotizaciones.last()
    assert cotizacion_fecha.text == f"Cotización al {cotizacion_moneda.fecha}: "
    assert cotizacion_compra.text == float_format(cotizacion_moneda.importe_compra)
    assert cotizacion_venta.text == float_format(cotizacion_moneda.importe_venta)

    # Debajo del nombre aparece una lista con las cotizaciones anteriores
    cotizaciones_historicas = browser.encontrar_elementos("class_row_cot")
    cotizaciones_bd = dolar.cotizaciones.reverse()
    for index, cot in enumerate(cotizaciones_bd):
        cot_mostrada = cotizaciones_historicas[index]
        assert cot_mostrada.encontrar_elemento("class_td_fecha", By.CLASS_NAME).text == str(cot.fecha)
        assert \
            cot_mostrada.encontrar_elemento("class_td_cot_compra", By.CLASS_NAME).text == \
            float_format(cot.importe_compra)
        assert \
            cot_mostrada.encontrar_elemento("class_td_cot_venta", By.CLASS_NAME).text == \
            float_format(cot.importe_venta)

    # En cada cotización hay un menú que nos permite editarla o eliminarla
    current_url = urlparse(browser.current_url).path
    cot_muestra = cotizaciones_bd[0]
    browser.verificar_link(
        nombre="mod_cot",
        viewname="cot_mod",
        args=[cot_muestra.sk],
        querydict={"next": current_url},
        criterio=By.CLASS_NAME,
    )
    browser.verificar_link(
        nombre="elim_cot",
        viewname="cot_elim",
        args=[cot_muestra.sk],
        querydict={"next": current_url},
        criterio=By.CLASS_NAME,
    )

    # Al inicio de la lista hay un botón que, al cliquear en él, nos lleva al form de cotización para cargar una
    # cotización nueva
    browser.verificar_link(
        nombre="cot_nueva",
        viewname="mon_cot_nueva",
        args=[dolar.sk],
        querydict={"next": current_url},
    )

    # Al final de la lista aparece un link que, al cliquear en él, nos lleva a la página principal
    browser.verificar_link(nombre="home", viewname="home")

def test_detalle_moneda_paginacion(browser, dolar, mas_de_20_cotizaciones_dolar):
    # Si hay más de 20 cotizaciones, se muestran sólo las últimas 20
    browser.ir_a_pag(dolar.get_absolute_url())
    cotizaciones = browser.encontrar_elementos("class_row_cot")
    assert len(cotizaciones) == 20

    # Al comienzo de la sección de cotizaciones hay una barra de navegación
    # que nos permite ver cotizaciones anteriores
    navigator = browser.encontrar_elemento("id_div_navigator_init")

    nros_pagina = navigator.encontrar_elementos("class_li_pagina_nro")
    assert [int(x.text) for x in nros_pagina] == [2]

    # Si cliqueamos en el número 2, vemos las cotizaciones inmediatamente anteriores
    nros_pagina[0].click()
    assert urlparse(browser.current_url).query == "page=2"
    fechas_cotizacion = [x.text for x in browser.encontrar_elementos("class_td_fecha")]
    assert mas_de_20_cotizaciones_dolar.first().fecha.strftime("%Y-%m-%d") in fechas_cotizacion
