from urllib.parse import urlparse

import pytest

from django.urls import reverse

from diario.models import Cuenta, Titular, Movimiento
from diario.utils.utils_saldo import saldo_general_historico
from utils.helpers_tests import fecha2page
from utils.numeros import float_format


@pytest.fixture
def mock_titular_principal(mocker, titular):
    return mocker.patch('diario.forms.TITULAR_PRINCIPAL', titular.sk)


def test_detalle_movimiento(browser, entrada, salida, traspaso, cuenta_acumulativa):
    browser.ir_a_pag()
    links_movimiento = browser.esperar_elementos("class_link_movimiento")

    # Cuando cliqueamos en un movimiento, el movimiento aparece como
    # seleccionado
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" not in movimientos[1].get_attribute("class")
    links_movimiento[1].click()
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movimientos[1].get_attribute("class")

    # Y en el saldo de la página aparece el saldo histórico al momento del
    # movimiento seleccionado
    assert \
        browser.esperar_elemento("id_importe_saldo_gral").text == \
        float_format(saldo_general_historico(salida))

    # Y al lado de cada cuenta aparece el saldo de la cuenta al momento del
    # movimiento seleccionado
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_saldo_cuenta")]
    for index, cta in enumerate([x for x in Cuenta.todes() if x.cta_madre is None]):
        assert saldos_historicos[index] == float_format(cta.saldo(salida))

    # Y al lado de cada titular aparece el capital del titular al momento del
    # movimiento seleccionado
    capitales_historicos = [
        x.text for x in browser.esperar_elementos("class_capital_titular")]
    for index, titular in enumerate(Titular.todes()):
        assert capitales_historicos[index] == float_format(titular.capital(salida))


def test_detalle_movimiento_en_cuenta_acumulativa(
        browser, titular, otro_titular, mock_titular_principal, fecha):
    # Creamos una cuenta
    browser.ir_a_pag(reverse('cta_nueva'))
    browser.completar_form(
        nombre="cuenta",
        sk="c",
        fecha_creacion=fecha,
    )
    cuenta = Cuenta.tomar(sk='c')

    # La dividimos en dos subcuentas con saldo cero
    browser.ir_a_pag(reverse('cta_div', args=cuenta.sk))
    browser.completar_form(
        fecha=fecha,
        form_0_nombre='primera subcuenta',
        form_0_sk='psc',
        form_0_saldo='0',
        form_0_titular=titular.nombre,
        form_1_nombre='segunda subcuenta',
        form_1_sk='ssc',
        form_1_titular=otro_titular.nombre,
    )
    sc1 = Cuenta.tomar(sk='psc')
    sc2 = Cuenta.tomar(sk='ssc')

    # Cargamos un saldo a la primera subcuenta por medio de un movimiento
    browser.ir_a_pag(reverse('mov_nuevo'))
    browser.completar_form(
        fecha=f'{fecha.year}-{fecha.month:02d}-{fecha.day:02d}',
        concepto='Saldo al inicio sc1',
        importe='110',
        cta_entrada=sc1.nombre
    )

    # Id para la segunda subcuenta
    browser.ir_a_pag(reverse('mov_nuevo'))
    browser.completar_form(
        fecha=f'{fecha.year}-{fecha.month:02d}-{fecha.day:02d}',
        concepto='Saldo al inicio sc2',
        importe='88',
        cta_entrada=sc2.nombre
    )
    mov1 = Movimiento.tomar(concepto='Saldo al inicio sc1')
    mov2 = Movimiento.tomar(concepto='Saldo al inicio sc2')

    link_mov_1 = browser.esperar_elemento(f'id_link_mov_{mov1.sk}')
    link_mov_1.click()
    saldo_sc1 = browser.esperar_elemento(f'id_saldo_cta_psc_{cuenta.moneda.sk}')
    saldo_sc2 = browser.esperar_elemento(f'id_saldo_cta_ssc_{cuenta.moneda.sk}')
    saldo_c = browser.esperar_saldo_en_moneda_de_cuenta('c')
    assert saldo_sc1.text == '110,00'
    assert saldo_sc2.text == '0,00'
    assert saldo_c.text == '110,00'

    link_mov_2 = browser.esperar_elemento(f'id_link_mov_{mov2.sk}')
    link_mov_2.click()
    saldo_sc1 = browser.esperar_elemento(f'id_saldo_cta_psc_{cuenta.moneda.sk}')
    saldo_sc2 = browser.esperar_elemento(f'id_saldo_cta_ssc_{cuenta.moneda.sk}')
    saldo_c = browser.esperar_saldo_en_moneda_de_cuenta('c')
    assert saldo_sc1.text == '110,00'
    assert saldo_sc2.text == '88,00'
    assert saldo_c.text == '198,00'


def pkfromlink(href: str) -> int:
    return int(urlparse(href).path.split("/")[-1])


@pytest.mark.parametrize("origen, destino", [
    ("/", "/diario/m/"),
    ("/diario/c/c/", "/diario/cm/c/"),
    ("/diario/t/titular/", "/diario/tm/titular/")])
def test_detalle_movimiento_en_paginas_anteriores(browser, muchos_dias, origen, destino):
    # Cuando estando en una página anterior cliqueamos en un movimiento...
    browser.ir_a_pag(origen + "?page=2")

    links_movimiento = browser.esperar_elementos("class_link_movimiento")

    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" not in movimientos[1].get_attribute("class")

    pk = pkfromlink(links_movimiento[1].get_attribute('href'))
    links_movimiento[1].click()

    # ...permanecemos en la página en la que estábamos...
    browser.assert_url(f"{destino}{pk}?page=2")

    # ...y el movimiento aparece resaltado.
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movimientos[1].get_attribute("class")

    # Cuando pasamos a otra página, se pierde el movimiento seleccionado
    # y se selecciona el último movimiento de la nueva página
    browser.pulsar("id_link_anterior_init")
    links_movimiento = browser.esperar_elementos("class_link_movimiento")

    browser.assert_url(f"{destino}{pkfromlink(links_movimiento[0].get_attribute('href'))}?page=1")


@pytest.mark.parametrize("origen", [None, "cuenta", "titular"])
def test_detalle_movimiento_en_fechas_anteriores(browser, muchos_dias, fecha, origen, request):
    ente = request.getfixturevalue(origen) if origen else None
    dias = ente.dias() if ente else muchos_dias
    url_origen = ente.get_absolute_url() if ente else reverse("home")
    # Cuando estando en la página de una fecha anterior cliqueamos en un movimiento...
    browser.ir_a_pag(f"{url_origen}?fecha={fecha}")
    links_movimiento = browser.esperar_elementos("class_link_movimiento")

    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" not in movimientos[1].get_attribute("class")

    sk_mov = int(urlparse(links_movimiento[1].get_attribute("href")).path.split("/")[-1])
    mov = Movimiento.tomar(sk=sk_mov)
    url_destino = mov.get_url(ente)
    links_movimiento[1].click()

    # ...permanecemos en la página en la que estábamos...
    browser.assert_url(f"{url_destino}?page={fecha2page(dias, fecha)}")

    # ...y el movimiento aparece resaltado...
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movimientos[1].get_attribute("class")
