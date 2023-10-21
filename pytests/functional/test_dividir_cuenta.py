import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By


def test_dividir_cuenta(browser, cuenta, otro_titular):
    # Vamos a la página de dividir cuenta y completamos los campos del formulario:
    browser.ir_a_pag(reverse('cta_div', args=[cuenta.slug]))
    browser.completar_form(**{
        'form_0_nombre': 'primera subcuenta',
        'form_0_slug': 'psc',
        'form_0_saldo': 0,
        'form_0_titular': cuenta.titular.nombre,
        'form_1_nombre': 'segunda subcuenta',
        'form_1_slug': 'ssc',
        'form_1_titular': otro_titular.nombre,
        'form_1_esgratis': True
    })

    # Somos dirigidos a la página de la cuenta, donde comprobamos que
    # ahora incluye las dos subcuentas recién creadas
    browser.assert_url(reverse('cuenta', args=[cuenta.slug]))
    titulo = browser.esperar_elemento('id_titulo_saldo_gral').text
    assert cuenta.nombre in titulo
    subcuentas = [
        sc.text for sc in browser.esperar_elementos('class_link_cuenta')
    ]
    assert subcuentas == ['primera subcuenta', 'segunda subcuenta']


def test_dividir_cuenta_con_saldo_y_fecha(
        browser, cuenta_con_saldo, otro_titular, importe_bajo, fecha_posterior):
    # Vamos a la página de dividir cuenta y completamos los campos del formulario,
    # incluyendo fecha y un saldo distinto de cero:
    browser.ir_a_pag(reverse('cta_div', args=[cuenta_con_saldo.slug]))
    browser.completar_form(**{
        'fecha': fecha_posterior,
        'form_0_nombre': 'primera subcuenta',
        'form_0_slug': 'psc',
        'form_0_saldo': importe_bajo,
        'form_0_titular': cuenta_con_saldo.titular.nombre,
        'form_1_nombre': 'segunda subcuenta',
        'form_1_slug': 'ssc',
        'form_1_titular': otro_titular.nombre,
        'form_1_esgratis': True
    })

    # Al ser dirigidos a la página de detalle de cuenta, vemos que esta incluye
    # los movimientos de traspaso correspondientes, y que la fecha de esos
    # movimientos corresponde a la fecha ingresada en el formulario.
    subcuentas = [
        sc.text for sc in browser.esperar_elementos('class_link_cuenta')
    ]
    assert subcuentas == ['primera subcuenta', 'segunda subcuenta']
    fechas_movimiento = [
        m.esperar_elemento('class_td_fecha', By.CLASS_NAME).text.strip()
        for m in browser.esperar_elementos('class_row_mov')
        if m.esperar_elemento(
            'class_td_concepto', By.CLASS_NAME
        ).text.strip() == 'Traspaso de saldo'
    ]
    assert len(fechas_movimiento) == 2
    for fm in fechas_movimiento:
        assert fm ==  fecha_posterior.strftime('%Y-%m-%d')
