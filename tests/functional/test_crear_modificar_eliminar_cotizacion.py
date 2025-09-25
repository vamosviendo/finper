from django.urls import reverse
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from utils.numeros import float_format


def test_crear_cotizacion(browser, dolar, fecha, fecha_anterior):
    """ Cuando vamos a la página de cotización nueva y completamos el formulario,
        si la nueva cotización es de fecha posterior a la última cotización anterior,
        aparece la nueva cotización como cotización de la moneda.
        Si es de fecha anterior a la última cotización anterior, se muestra la
        cotización que ya se mostraba. La nueva cotización aparece en la lista de
        cotizaciones anteriores.
    """
    browser.ir_a_pag(dolar.get_absolute_url())
    ultima_fecha = browser.esperar_elemento("class_td_fecha", By.CLASS_NAME).text
    assert ultima_fecha != fecha.strftime("%Y-%m-%d")

    # Dada una moneda, cargamos una cotización nueva con fecha posterior a todas
    # las otras cotizaciones de la moneda.
    browser.ir_a_pag(reverse("mon_cot_nueva", args=[dolar.sk]))
    browser.completar_form(
        fecha=fecha,
        importe_compra=1000000,
        importe_venta=1100000
    )

    # Al terminar de cargar la cotización nueva, somos redirigidos a la página
    # de detalle de la moneda.
    browser.assert_url(dolar.get_absolute_url())

    # En el encabezado de la página, aparece el importe de la cotización nueva
    cotizacion_c_en_detalle = browser.esperar_elemento("id_cotizacion_compra").text
    cotizacion_v_en_detalle = browser.esperar_elemento("id_cotizacion_venta").text
    assert cotizacion_c_en_detalle == float_format(1000000)
    assert cotizacion_v_en_detalle == float_format(1100000)

    # La cotización nueva aparece al principio de la lista de cotizaciones de
    # la moneda.
    ultima_fecha = browser.esperar_elemento("class_td_fecha", By.CLASS_NAME).text
    assert ultima_fecha == fecha.strftime("%Y-%m-%d")

    # En la página principal, en la lista de monedas aparece el importe de la
    # cotización nueva al lado del nombre de la moneda.
    browser.ir_a_pag(reverse("home"))
    cotizacion_c = browser.esperar_elemento(f"id_cotizacion_c_{dolar.sk}").text
    cotizacion_v = browser.esperar_elemento(f"id_cotizacion_v_{dolar.sk}").text
    assert cotizacion_c == float_format(1000000)
    assert cotizacion_v == float_format(1100000)

    browser.ir_a_pag(dolar.get_absolute_url())
    fechas = [x.text for x in browser.esperar_elementos("class_td_fecha")]
    assert fecha_anterior.strftime("%Y-%m-%d") not in fechas
    # Si cargamos una cotización de fecha anterior a la ultima cotización de la fecha...
    browser.ir_a_pag(reverse("mon_cot_nueva", args=[dolar.sk]))
    browser.completar_form(
        fecha=fecha_anterior,
        importe_compra=20000,
        importe_venta=25000
    )

    # ...en el encabezado de la página sigue apareciendo la misma cotización que antes
    assert browser.esperar_elemento("id_cotizacion_compra").text == cotizacion_c_en_detalle
    assert browser.esperar_elemento("id_cotizacion_venta").text == cotizacion_v_en_detalle

    # La cotización nueva aparece entre las cotizaciones de la lista de cotizaciones
    # de la moneda
    fechas = [x.text for x in browser.esperar_elementos("class_td_fecha")]
    assert fecha_anterior.strftime("%Y-%m-%d") in fechas

    # En la página principal, al lado del nombre de la moneda tampoco cambian los
    # importes de la cotización.
    browser.ir_a_pag(reverse("home"))
    cotizacion_c_nueva = browser.esperar_elemento(f"id_cotizacion_c_{dolar.sk}").text
    cotizacion_v_nueva = browser.esperar_elemento(f"id_cotizacion_v_{dolar.sk}").text
    assert cotizacion_c_nueva == cotizacion_c
    assert cotizacion_v_nueva == cotizacion_v

    # Si intentamos crear una cotización con una fecha ya existente, recibimos
    # un mensaje de error.
    browser.ir_a_pag(reverse("mon_cot_nueva", args=[dolar.sk]))
    browser.completar_form(
        fecha=fecha_anterior,
        importe_compra=20010,
        importe_venta=20020
    )
    errors = browser.esperar_elemento("id_form_cotizacion").esperar_elemento("errorlist", By.CLASS_NAME)
    assert "Ya existe una cotización para esta moneda en la fecha seleccionada" in errors.text


def test_modificar_cotizacion(browser, dolar, cotizacion_dolar, cotizacion_posterior_dolar, cotizacion_tardia_dolar):
    """ Dada una moneda con más de una cotización
        Si modificamos el importe de la última cotización, este cambio se ve
        reflejado en la lista de cotizaciones y en el encabezado de la página.
        Si cambiamos la fecha de una cotización antigua por una fecha anterior
        a la de la última cotización, vemos ese cambio reflejado en la lista
        de cotizaciones.
        Si cambiamos la fecha de una cotización antigua por una fecha posterior
        a la de la última cotización, vemos reflejado el cambio en la lista
        de cotizaciones y los importes de la cotización modificada aparecen
        en el encabezado.
        Si cambiamos la fecha de la última cotización por una fecha anterior
        a la de la cotización anterior, los importes en el encabezado son
        reemplazados por los de la cotización anterior a la última
        Si intentamos cambiar la fecha de una cotización por una fecha que
        ya tenga otra cotización, recibimos un mensaje de error.
    """
    # Dada una moneda con más de una cotización

    # Si modificamos el importe de una cotización antigua, este cambio se ve
    # reflejado en la lista de cotizaciones.
    browser.ir_a_pag(dolar.get_absolute_url())
    cotizacion = browser.esperar_cotizacion(cotizacion_dolar.fecha)
    importe_compra = cotizacion.esperar_elemento("class_td_cot_compra", By.CLASS_NAME).text
    importe_venta = cotizacion.esperar_elemento("class_td_cot_venta", By.CLASS_NAME).text
    assert importe_compra != float_format(400)
    assert importe_venta != float_format(450)

    browser.ir_a_pag(reverse("cot_mod", args=[cotizacion_dolar.pk]))
    browser.completar("id_importe_compra", 400)
    browser.completar("id_importe_venta", 450)
    browser.pulsar()
    cotizacion = browser.esperar_cotizacion(cotizacion_dolar.fecha)
    importe_compra = cotizacion.esperar_elemento("class_td_cot_compra", By.CLASS_NAME).text
    importe_venta = cotizacion.esperar_elemento("class_td_cot_venta", By.CLASS_NAME).text
    assert importe_compra == float_format(400)
    assert importe_venta == float_format(450)

def test_eliminar_cotizacion():
    """ Dada una moneda con más de una cotización
        Si eliminamos una cotización antigua, ésta desaparece de la lista
        Si eliminamos la última cotización, ésta desaparece de la lista y
        los importes en el encabezado son reeemplazados por los de la cotización
        anterior a la última

        Dada una moneda con una única cotización
        Si eliminamos la cotización, recibimos un mensaje de error.
    """
    ...
