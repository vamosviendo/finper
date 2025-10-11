from datetime import timedelta

from django.urls import reverse
from selenium.webdriver.common.by import By

from utils.numeros import float_format


def test_crear_cotizacion(browser, dolar, fecha, fecha_anterior):
    browser.ir_a_pag(dolar.get_absolute_url())
    ultima_fecha = browser.encontrar_elemento("class_td_fecha", By.CLASS_NAME).text
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
    cotizacion_c_en_detalle = browser.encontrar_elemento("id_cotizacion_compra").text
    cotizacion_v_en_detalle = browser.encontrar_elemento("id_cotizacion_venta").text
    assert cotizacion_c_en_detalle == float_format(1000000)
    assert cotizacion_v_en_detalle == float_format(1100000)

    # La cotización nueva aparece al principio de la lista de cotizaciones de
    # la moneda.
    ultima_fecha = browser.encontrar_elemento("class_td_fecha", By.CLASS_NAME).text
    assert ultima_fecha == fecha.strftime("%Y-%m-%d")

    # En la página principal, en la lista de monedas aparece el importe de la
    # cotización nueva al lado del nombre de la moneda.
    browser.ir_a_pag(reverse("home"))
    cotizacion_c = browser.encontrar_elemento(f"id_cotizacion_c_{dolar.sk}").text
    cotizacion_v = browser.encontrar_elemento(f"id_cotizacion_v_{dolar.sk}").text
    assert cotizacion_c == float_format(1000000)
    assert cotizacion_v == float_format(1100000)

    browser.ir_a_pag(dolar.get_absolute_url())
    fechas = [x.text for x in browser.encontrar_elementos("class_td_fecha")]
    assert fecha_anterior.strftime("%Y-%m-%d") not in fechas
    # Si cargamos una cotización de fecha anterior a la ultima cotización de la fecha...
    browser.ir_a_pag(reverse("mon_cot_nueva", args=[dolar.sk]))
    browser.completar_form(
        fecha=fecha_anterior,
        importe_compra=20000,
        importe_venta=25000
    )

    # ...en el encabezado de la página sigue apareciendo la misma cotización que antes
    assert browser.encontrar_elemento("id_cotizacion_compra").text == cotizacion_c_en_detalle
    assert browser.encontrar_elemento("id_cotizacion_venta").text == cotizacion_v_en_detalle

    # La cotización nueva aparece entre las cotizaciones de la lista de cotizaciones
    # de la moneda
    fechas = [x.text for x in browser.encontrar_elementos("class_td_fecha")]
    assert fecha_anterior.strftime("%Y-%m-%d") in fechas

    # En la página principal, al lado del nombre de la moneda tampoco cambian los
    # importes de la cotización.
    browser.ir_a_pag(reverse("home"))
    cotizacion_c_nueva = browser.encontrar_elemento(f"id_cotizacion_c_{dolar.sk}").text
    cotizacion_v_nueva = browser.encontrar_elemento(f"id_cotizacion_v_{dolar.sk}").text
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
    errors = browser.encontrar_elemento("id_form_cotizacion").encontrar_elemento("errorlist", By.CLASS_NAME)
    assert "Ya existe una cotización para esta moneda en la fecha seleccionada" in errors.text


class TestModificarCotizacion:

    def test_si_cambian_importes_de_cotizacion_anterior_cambian_importes_en_lista_no_en_encabezado(
            self, browser, dolar, cotizacion_dolar):
        # Si modificamos el importe de una cotización antigua, este cambio se ve
        # reflejado en la lista de cotizaciones.
        browser.ir_a_pag(dolar.get_absolute_url())
        cotizacion = browser.encontrar_cotizacion(cotizacion_dolar.fecha)
        importe_compra = cotizacion.encontrar_elemento("class_td_cot_compra", By.CLASS_NAME).text
        importe_venta = cotizacion.encontrar_elemento("class_td_cot_venta", By.CLASS_NAME).text
        assert importe_compra != float_format(400)
        assert importe_venta != float_format(450)

        browser.ir_a_pag(cotizacion_dolar.get_edit_url())
        browser.completar("id_importe_compra", 400)
        browser.completar("id_importe_venta", 450)
        browser.pulsar()
        cotizacion = browser.encontrar_cotizacion(cotizacion_dolar.fecha)
        importe_compra = cotizacion.encontrar_elemento("class_td_cot_compra", By.CLASS_NAME).text
        importe_venta = cotizacion.encontrar_elemento("class_td_cot_venta", By.CLASS_NAME).text
        assert importe_compra == float_format(400)
        assert importe_venta == float_format(450)

    def test_si_cambian_importes_de_ultima_cotizacion_cambian_importes_en_encabezado(
            self, browser, dolar, cotizacion_tardia_dolar):
        # Si modificamos el importe de la última cotización, este cambio se ve
        # reflejado en la lista de cotizaciones y en el encabezado de la página.
        browser.ir_a_pag(dolar.get_absolute_url())
        importe_compra_encabezado = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_encabezado = browser.encontrar_elemento("id_cotizacion_venta").text
        assert importe_compra_encabezado == float_format(cotizacion_tardia_dolar.importe_compra)
        assert importe_venta_encabezado == float_format(cotizacion_tardia_dolar.importe_venta)
        importe_compra = browser.encontrar_elemento("class_td_cot_compra", By.CLASS_NAME).text
        importe_venta = browser.encontrar_elemento("class_td_cot_venta", By.CLASS_NAME).text
        assert importe_compra != float_format(1800)
        assert importe_venta != float_format(1850)

        browser.ir_a_pag(cotizacion_tardia_dolar.get_edit_url())
        browser.completar("id_importe_compra", 1800)
        browser.completar("id_importe_venta", 1850)
        browser.pulsar()
        importe_compra_encabezado = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_encabezado = browser.encontrar_elemento("id_cotizacion_venta").text
        assert importe_compra_encabezado == float_format(1800)
        assert importe_venta_encabezado == float_format(1850)
        importe_compra = browser.encontrar_elemento("class_td_cot_compra", By.CLASS_NAME).text
        importe_venta = browser.encontrar_elemento("class_td_cot_venta", By.CLASS_NAME).text
        assert importe_compra == float_format(1800)
        assert importe_venta == float_format(1850)

    def test_si_cambia_fecha_de_una_cotizacion_anterior_por_fecha_anterior_a_la_ultima_no_cambian_importes_en_encabezado(
            self, browser, dolar, cotizacion_dolar, cotizacion_posterior_dolar, cotizacion_tardia_dolar):
        # Si cambiamos la fecha de una cotización antigua por una fecha anterior
        # a la de la última cotización, vemos ese cambio reflejado en la lista
        # de cotizaciones. Los importes del encabezado no cambian.
        browser.ir_a_pag(dolar.get_absolute_url())
        importe_compra_encabezado = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_encabezado = browser.encontrar_elemento("id_cotizacion_venta").text
        fechas_pag = [x.text for x in browser.encontrar_elementos("class_td_fecha")]
        fecha_nueva = cotizacion_tardia_dolar.fecha - timedelta(2)
        assert fecha_nueva.strftime("%Y-%m-%d") not in fechas_pag

        browser.ir_a_pag(cotizacion_dolar.get_edit_url())
        browser.completar("id_fecha", fecha_nueva)
        browser.pulsar()
        importe_compra_enc_nuevo = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_enc_nuevo = browser.encontrar_elemento("id_cotizacion_venta").text
        fechas_pag = [x.text for x in browser.encontrar_elementos("class_td_fecha")]
        assert importe_compra_enc_nuevo == importe_compra_encabezado
        assert importe_venta_enc_nuevo == importe_venta_encabezado
        assert fecha_nueva.strftime("%Y-%m-%d") in fechas_pag

    def test_si_cambia_fecha_de_cotizacion_anterior_por_fecha_posterior_a_la_ultima_cambian_importes_en_encabezado(
            self, browser, dolar, cotizacion_posterior_dolar, cotizacion_tardia_dolar):
        # Si cambiamos la fecha de una cotización antigua por una fecha posterior
        # a la de la última cotización, los importes de la cotización modificada
        # aparecen en el encabezado.
        browser.ir_a_pag(dolar.get_absolute_url())
        importe_compra_encabezado = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_encabezado = browser.encontrar_elemento("id_cotizacion_venta").text
        assert importe_compra_encabezado != float_format(cotizacion_posterior_dolar.importe_compra)
        assert importe_venta_encabezado != float_format(cotizacion_posterior_dolar.importe_venta)

        browser.ir_a_pag(cotizacion_posterior_dolar.get_edit_url())
        browser.completar("id_fecha", cotizacion_tardia_dolar.fecha + timedelta(2))
        browser.pulsar()
        importe_compra_encabezado = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_encabezado = browser.encontrar_elemento("id_cotizacion_venta").text
        assert importe_compra_encabezado == float_format(cotizacion_posterior_dolar.importe_compra)
        assert importe_venta_encabezado == float_format(cotizacion_posterior_dolar.importe_venta)

    def test_si_cambia_fecha_de_ultima_cotizacion_por_fecha_anterior_a_cotizacion_anterior_cambian_importes_en_encabezado(
            self, browser, dolar, cotizacion_posterior_dolar, cotizacion_tardia_dolar):
        # Si cambiamos la fecha de la última cotización por una fecha anterior
        # a la de la cotización anterior, los importes en el encabezado son
        # reemplazados por los de la cotización anterior a la última
        browser.ir_a_pag(cotizacion_posterior_dolar.get_edit_url())
        browser.completar("id_fecha", cotizacion_tardia_dolar.fecha - timedelta(1))
        browser.pulsar()
        importe_compra_encabezado = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_encabezado = browser.encontrar_elemento("id_cotizacion_venta").text
        assert importe_compra_encabezado == float_format(cotizacion_tardia_dolar.importe_compra)
        assert importe_venta_encabezado == float_format(cotizacion_tardia_dolar.importe_venta)

    def test_no_permite_cambiar_fecha_de_cotizacion_por_fecha_de_cotizacion_existente(
            self, browser, dolar, cotizacion_posterior_dolar, cotizacion_tardia_dolar):
        # Si intentamos cambiar la fecha de una cotización por una fecha que
        # ya tenga otra cotización, recibimos un mensaje de error.
        browser.ir_a_pag(cotizacion_posterior_dolar.get_edit_url())
        browser.completar("id_fecha", cotizacion_tardia_dolar.fecha)
        browser.pulsar()
        errors = browser.encontrar_elemento("id_form_cotizacion").encontrar_elemento("errorlist", By.CLASS_NAME)
        assert "Ya existe una cotización para esta moneda en la fecha seleccionada" in errors.text


class TestEliminarCotizacion:
    def test_eliminar_cotizacion(self):
        """ Dada una moneda con más de una cotización
            Si eliminamos la última cotización, ésta desaparece de la lista y
            los importes en el encabezado son reeemplazados por los de la cotización
            anterior a la última

            Dada una moneda con una única cotización
            Si eliminamos la cotización, recibimos un mensaje de error.
        """
        ...

    def test_si_se_elimina_cotizacion_antigua_desaparece_de_la_lista_y_no_cambian_importes_en_encabezado(
            self, browser, dolar, cotizacion_dolar, cotizacion_posterior_dolar):
        browser.ir_a_pag(dolar.get_absolute_url())
        importe_compra_encabezado = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_encabezado = browser.encontrar_elemento("id_cotizacion_venta").text
        cotizaciones = [x.text.split(" ")[:3] for x in browser.encontrar_elementos("class_row_cot")]
        cotizacion_a_eliminar = [
            cotizacion_dolar.fecha.strftime("%Y-%m-%d"),
            float_format(cotizacion_dolar.importe_compra),
            float_format(cotizacion_dolar.importe_venta),
        ]
        assert cotizacion_a_eliminar in cotizaciones

        browser.ir_a_pag(cotizacion_dolar.get_delete_url())
        browser.pulsar("id_btn_confirm")
        cotizaciones = [x.text.split(" ")[:3] for x in browser.encontrar_elementos("class_row_cot")]
        assert cotizacion_a_eliminar not in cotizaciones
        importe_compra_nuevo = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_nuevo = browser.encontrar_elemento("id_cotizacion_venta").text
        assert importe_compra_nuevo == importe_compra_encabezado
        assert importe_venta_nuevo == importe_venta_encabezado

    def test_si_se_elimina_ultima_cotizacion_importes_del_encabezado_son_reemplazados_por_los_de_cotizacion_anterior(
            self, browser, dolar, cotizacion_dolar, cotizacion_posterior_dolar):
        assert cotizacion_dolar.importe_compra != cotizacion_posterior_dolar.importe_compra
        assert cotizacion_dolar.importe_venta != cotizacion_posterior_dolar.importe_venta

        browser.ir_a_pag(dolar.get_absolute_url())
        importe_compra_encabezado = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_encabezado = browser.encontrar_elemento("id_cotizacion_venta").text
        assert importe_compra_encabezado == float_format(cotizacion_posterior_dolar.importe_compra)
        assert importe_venta_encabezado == float_format(cotizacion_posterior_dolar.importe_venta)

        browser.ir_a_pag(cotizacion_posterior_dolar.get_delete_url())
        browser.pulsar("id_btn_confirm")
        importe_compra_nuevo = browser.encontrar_elemento("id_cotizacion_compra").text
        importe_venta_nuevo = browser.encontrar_elemento("id_cotizacion_venta").text
        assert importe_compra_nuevo == float_format(cotizacion_dolar.importe_compra)
        assert importe_venta_nuevo == float_format(cotizacion_dolar.importe_venta)
