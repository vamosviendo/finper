from django.urls import reverse

from utils.numeros import float_format


def test_crear_cotizacion(browser, dolar, fecha, fecha_anterior):
    """ Cuando vamos a la página de cotización nueva y completamos el formulario,
        si la nueva cotización es de fecha posterior a la última cotización anterior,
        aparece la nueva cotización como cotización de la moneda.
        Si es de fecha anterior a la última cotización anterior, se muestra la
        cotización que ya se mostraba.
    """
    browser.ir_a_pag(reverse("home"))
    cotizacion_c_vieja = browser.esperar_elemento(f"id_cotizacion_c_{dolar.sk}").text
    cotizacion_v_vieja = browser.esperar_elemento(f"id_cotizacion_v_{dolar.sk}").text

    browser.ir_a_pag(reverse("mon_cot_nueva", args=[dolar.sk]))
    browser.completar_form(
        fecha=fecha,
        importe_compra=1000000,
        importe_venta=1100000
    )
    cotizacion_c = browser.esperar_elemento(f"id_cotizacion_c_{dolar.sk}").text
    cotizacion_v = browser.esperar_elemento(f"id_cotizacion_v_{dolar.sk}").text
    assert cotizacion_c != cotizacion_c_vieja
    assert cotizacion_v != cotizacion_v_vieja
    assert cotizacion_c == float_format(1000000)
    assert cotizacion_v == float_format(1100000)

    browser.ir_a_pag(reverse("mon_cot_nueva", args=[dolar.sk]))
    browser.completar_form(
        fecha=fecha_anterior,
        importe_compra=20000,
        importe_venta=25000
    )
    cotizacion_c_nueva = browser.esperar_elemento(f"id_cotizacion_c_{dolar.sk}").text
    cotizacion_v_nueva = browser.esperar_elemento(f"id_cotizacion_v_{dolar.sk}").text
    assert cotizacion_c_nueva == cotizacion_c
    assert cotizacion_v_nueva == cotizacion_v


def test_modificar_cotizacion():
    ...


def test_eliminar_cotizacion():
    ...
