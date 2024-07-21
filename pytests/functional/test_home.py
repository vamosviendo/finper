from __future__ import annotations

from django.urls import reverse
from selenium.webdriver.common.by import By

from diario.models import Movimiento, Dia
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

    # En la sección de movimientos vemos dos divisiones de día.
    # Cada una de ellas tiene un título con la fecha y el saldo del día
    # Debajo del título hay una tabla con todos los movimientos del día.
    divs_dia = browser.find_elements_by_class_name("class_div_dia")
    assert len(divs_dia) == 2
    fechas_dia = texto_en_hijos_respectivos("class_span_fecha_dia", divs_dia)
    saldos_dia = texto_en_hijos_respectivos("class_span_saldo_dia", divs_dia)

    dias = Dia.todes()
    for i, dia in enumerate(dias.reverse()):
        dia_web = divs_dia[i]
        assert fechas_dia[i] == dia.str_dia_semana()
        assert saldos_dia[i] == float_format(dia.saldo())
        movs_dia = dia.movimientos
        movs_dia_web = dia_web.find_elements_by_class_name("class_row_mov")
        conceptos = texto_en_hijos_respectivos("class_td_concepto", movs_dia_web)
        detalles = texto_en_hijos_respectivos("class_td_detalle", movs_dia_web)
        importes = texto_en_hijos_respectivos("class_td_importe", movs_dia_web)
        ctas_entrada = texto_en_hijos_respectivos("class_td_cta_entrada", movs_dia_web)
        ctas_salida = texto_en_hijos_respectivos("class_td_cta_salida", movs_dia_web)
        for i, mov in enumerate(movs_dia):
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


def test_home_monedas(
        browser, cuenta_con_saldo, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros,
        peso, dolar, euro, request):
    # Vemos que al lado de cada cuenta aparece una columna por cada moneda, con
    # su saldo expresado en esa moneda. Si la moneda de la columna coincide con
    # la de la cuenta, aparece resaltada.
    browser.ir_a_pag()
    for cuenta in (cuenta_con_saldo, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros):
        for moneda in (peso, dolar, euro):
            saldo_mon = browser.esperar_elemento(f"id_saldo_cta_{cuenta.slug}_{moneda.monname}")
            assert saldo_mon.text == float_format(cuenta.saldo_en(moneda))
            classname = saldo_mon.get_attribute("class")
            if moneda == cuenta.moneda:
                assert "mon_cuenta" in classname
            else:
                assert "mon_cuenta" not in classname
    cuenta_acumulativa = request.getfixturevalue('cuenta_acumulativa')
    cuenta_acumulativa_en_dolares = request.getfixturevalue('cuenta_acumulativa_en_dolares')
    browser.ir_a_pag()

    # Esto también se aplica a las subcuentas de una cuenta acumulativa
    subcuentas = list(cuenta_acumulativa.subcuentas.all() | cuenta_acumulativa_en_dolares.subcuentas.all())
    for cuenta in subcuentas:
        for moneda in (peso, dolar, euro):
            saldo_mon = browser.esperar_elemento(f"id_saldo_cta_{cuenta.slug}_{moneda.monname}")
            assert saldo_mon.text == float_format(cuenta.saldo_en(moneda))
            classname = saldo_mon.get_attribute("class")
            if moneda == cuenta.moneda:
                assert "mon_cuenta" in classname
            else:
                assert "mon_cuenta" not in classname


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
        browser.verificar_link('mod_mov', 'mov_mod', [entrada.pk], By.CLASS_NAME)

        # cuando cliqueamos en el link de borrar movimiento, accedemos a la página de confirmación
        browser.verificar_link('elim_mov', 'mov_elim', [entrada.pk], By.CLASS_NAME)

    def test_seccion_monedas(self, browser, peso):

        # cuando cliqueamos en el link de moneda nueva, accedemos a la página para agregar movimiento
        browser.verificar_link('moneda_nueva', 'mon_nueva')

        # cuando cliqueamos en el link de editar movimiento, accedemos a la página de edición de ese movimiento
        browser.verificar_link(f'mon_mod_{peso.monname}', 'mon_mod', [peso.monname])

        # cuando cliqueamos en el link de borrar movimiento, accedemos a la página de confirmación
        browser.verificar_link(f'mon_elim_{peso.monname}', 'mon_elim', [peso.monname])
