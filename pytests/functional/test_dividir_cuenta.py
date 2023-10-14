import pytest
from django.urls import reverse


def test_dividir_cuenta(browser, cuenta, otro_titular):
    # Vamos a la página de dividir cuenta y completamos los campos del formulario:
    browser.ir_a_pag(reverse('cta_div', args=[cuenta.slug]))
    browser.completar_form(**{
        'form_0_nombre': 'primera subcuenta',
        'form_0_slug': 'psc',
        'form_0_saldo': 0,
        'form_0_titular': 'Titular',
        'form_1_nombre': 'segunda subcuenta',
        'form_1_slug': 'ssc',
        'form_1_titular': 'Otro Titular',
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
        browser, cuenta_con_saldo, otro_titular, importe, fecha):
    browser.ir_a_pag(reverse('cta_div', args=[cuenta_con_saldo.slug]))
    browser.completar_form(**{
        'fecha': fecha.strftime('%Y-%m-%d'),
        'form_0_nombre': 'primera subcuenta',
        'form_0_slug': 'psc',
        'form_0_saldo': 0,
        'form_0_titular': 'Titular',
        'form_1_nombre': 'segunda subcuenta',
        'form_1_slug': 'ssc',
        'form_1_titular': 'Otro Titular',
        'form_1_esgratis': True
    })
    pytest.fail('COMPLETAR')
