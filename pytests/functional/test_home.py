from __future__ import annotations

from django.urls import reverse
from selenium.webdriver.common.by import By

from diario.models import Movimiento
from .helpers import texto_en_hijos_respectivos
from utils.numeros import float_format


def test_home(
        browser, titular, otro_titular,
        cuenta, cuenta_2, cuenta_3, cuenta_acumulativa,
        entrada, traspaso, entrada_posterior_otra_cuenta):
    # Vamos a la página principal
    browser.ir_a_pag()

    # Vemos al tope de la página el saldo general, suma de todas las cuentas de
    # todos los titulares
    titulo_saldo = browser.esperar_elemento("id_titulo_saldo_gral").text.strip()
    assert titulo_saldo == "Saldo general:"
    saldo_gral = browser.esperar_elemento("id_importe_saldo_gral")
    assert saldo_gral.text == float_format(
        cuenta.saldo + cuenta_2.saldo + cuenta_3.saldo + cuenta_acumulativa.saldo
    )

    # Vemos dos titulares en el menú de titulares
    titulares = browser.esperar_elementos("class_div_titular")
    assert len(titulares) == 2
    nombres = texto_en_hijos_respectivos("class_div_nombre_titular", titulares)
    assert nombres[0] == titular.nombre
    assert nombres[1] == otro_titular.nombre

    # Vemos que al lado de cada titular aparece su capital
    capitales = texto_en_hijos_respectivos("class_capital_titular", titulares)
    assert capitales[0] == float_format(titular.capital)
    assert capitales[1] == float_format(otro_titular.capital)

    # Vemos seis cuentas en el menú de cuentas (4 cuentas y 2 subcuentas)
    cuentas = browser.find_elements_by_class_name("class_div_cuenta")
    assert len(cuentas) == 6
    nombres_cuenta = texto_en_hijos_respectivos("class_nombre_cuenta", cuentas)
    assert nombres_cuenta[0] == cuenta.nombre
    assert nombres_cuenta[1] == cuenta_2.nombre
    assert nombres_cuenta[2] == cuenta_3.nombre
    assert nombres_cuenta[3] == cuenta_acumulativa.nombre
    assert nombres_cuenta[4] == cuenta_acumulativa.subcuentas.first().nombre
    assert nombres_cuenta[5] == cuenta_acumulativa.subcuentas.last().nombre

    # Vemos que la cuenta acumulativa es presentada en un color más oscuro,
    # y las subcuentas en un color más claro
    tds_cuenta = browser.find_elements_by_class_name("class_td_cuenta")
    assert "acumulativa" in tds_cuenta[3].get_attribute("class")
    assert "class_td_subcuenta" in tds_cuenta[4].get_attribute("class")
    assert "class_td_subcuenta" in tds_cuenta[5].get_attribute("class")

    # A la derecha de cada una de las cuentas se ve su saldo, el cual
    # corresponde a los movimientos en los que participó
    saldos = texto_en_hijos_respectivos("class_saldo_cuenta", cuentas)
    assert saldos[0] == float_format(entrada.importe + traspaso.importe)
    assert saldos[1] == float_format(
        entrada_posterior_otra_cuenta.importe - traspaso.importe)
    assert saldos[2] == '0,00'

    # Vemos seis movimientos en la sección de movimientos, con conceptos
    # correspondientes al concepto de cada uno de los movimientos existentes.
    webelements_mov = browser.find_elements_by_class_name("class_row_mov")
    webelements_mov.reverse()
    objects_mov = Movimiento.todes()
    assert len(webelements_mov) == 6
    fechas = texto_en_hijos_respectivos("class_td_fecha", webelements_mov)
    conceptos = texto_en_hijos_respectivos("class_td_concepto", webelements_mov)
    detalles = texto_en_hijos_respectivos('class_td_detalle', webelements_mov)
    importes = texto_en_hijos_respectivos("class_td_importe", webelements_mov)
    ctas_entrada = texto_en_hijos_respectivos("class_td_cta_entrada", webelements_mov)
    ctas_salida = texto_en_hijos_respectivos("class_td_cta_salida", webelements_mov)

    for i, mov in enumerate(objects_mov):
        assert fechas[i] == mov.fecha.strftime('%Y-%m-%d')
        assert conceptos[i] == mov.concepto
        assert detalles[i] == ("" if mov.detalle is None else f"{mov.detalle[:49]}…")
        assert importes[i] == float_format(mov.importe)

        try:
            assert ctas_entrada[i] == mov.cta_entrada.nombre
        except AttributeError:
            assert ctas_entrada[i] == ""

        try:
            assert ctas_salida[i] == mov.cta_salida.nombre
        except AttributeError:
            assert ctas_salida[i] == ""


class TestHomeLinks:
    def test_seccion_titulares(self, browser, titular, otro_titular):

        # Cuando cliqueamos en un titular, vamos a la página de ese titular
        browser.ir_a_pag()
        browser.cliquear_en_titular(titular)
        browser.assert_url(reverse("titular", args=[titular.titname]))

        # cuando cliqueamos en el ícono de agregar titular, accedemos a la página para agregar titular nuevo
        browser.verificar_link('titular_nuevo', 'tit_nuevo')

        # cuando cliqueamos en el link de editar titular, accedemos a la página de edición de ese titular
        browser.verificar_link(f'tit_mod_{titular.titname}', 'tit_mod', [titular.titname])

        # cuando cliqueamos en el link de borrar titular, accedemos a la página de confirmación
        browser.verificar_link(f'tit_elim_{titular.titname}', 'tit_elim', [titular.titname])

    def test_seccion_cuentas(self, browser, cuenta, cuenta_2, cuenta_acumulativa):
        subcuenta = cuenta_acumulativa.subcuentas.first()

        # Cuando cliqueamos en una cuenta, vamos a la página de esa cuenta
        browser.ir_a_pag()
        browser.cliquear_en_cuenta(cuenta_2)
        browser.assert_url(reverse("cuenta", args=[cuenta_2.slug]))

        # Cuando cliqueamos en una subcuenta, vamos a la página de esa subcuenta
        browser.ir_a_pag()
        browser.cliquear_en_cuenta(subcuenta)
        browser.assert_url(reverse("cuenta", args=[subcuenta.slug]))

        # cuando cliqueamos en el ícono de agregar cuenta, accedemos a la página para agregar cuenta nueva
        browser.verificar_link('cuenta_nueva', 'cta_nueva')

        # cuando cliqueamos en el link de editar cuenta, accedemos a la página de edición de esa cuenta
        browser.verificar_link(f'cta_mod_{cuenta.slug}', 'cta_mod', [cuenta.slug])
        browser.verificar_link(f'cta_mod_{subcuenta.slug}', 'cta_mod', [subcuenta.slug])

        # cuando cliqueamos en el link de borrar cuenta, accedemos a la página de confirmación
        browser.verificar_link(f'cta_elim_{cuenta.slug}', 'cta_elim', [cuenta.slug])
        browser.verificar_link(f'cta_elim_{subcuenta.slug}', 'cta_elim', [subcuenta.slug])

    def test_seccion_movimientos(self, browser, entrada, salida):

        # cuando cliqueamos en el link de movimiento nuevo, accedemos a la página para agregar movimiento
        browser.verificar_link('mov_nuevo', 'mov_nuevo')

        # cuando cliqueamos en el link de editar movimiento, accedemos a la página de edición de ese movimiento
        browser.verificar_link('mod_mov', 'mov_mod', [salida.pk], By.CLASS_NAME)

        # cuando cliqueamos en el link de borrar movimiento, accedemos a la página de confirmación
        browser.verificar_link('elim_mov', 'mov_elim', [salida.pk], By.CLASS_NAME)
