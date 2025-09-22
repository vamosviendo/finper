from __future__ import annotations

from datetime import date, timedelta
from urllib.parse import urlparse

from django.urls import reverse
from selenium.webdriver.common.by import By

from diario.models import Dia
from utils.helpers_tests import fecha2page
from utils.tiempo import str2date
from .helpers import texto_en_hijos_respectivos
from utils.numeros import float_format


def test_home(
        browser, titular, otro_titular,
        cuenta, cuenta_2, cuenta_3, cuenta_acumulativa,
        entrada, traspaso, entrada_posterior_otra_cuenta,
        fecha, fecha_tardia,
        muchos_dias):
    # Vamos a la página principal
    browser.ir_a_pag()

    # Vemos al tope de la página el saldo general, suma de todas las cuentas de
    # todos los titulares
    titulo_saldo = browser.esperar_elemento("id_titulo_saldo_gral").text.strip()
    assert titulo_saldo == "Saldo general:"
    saldo_gral = browser.esperar_elemento("id_importe_saldo_gral")
    assert saldo_gral.text == float_format(
        cuenta.saldo() + cuenta_2.saldo() + cuenta_3.saldo() + cuenta_acumulativa.saldo()
    )

    # Vemos dos titulares en el menú de titulares
    titulares = browser.esperar_elementos("class_div_titular")
    assert len(titulares) == 2
    nombres = texto_en_hijos_respectivos("class_div_nombre_titular", titulares)
    assert nombres[0] == titular.nombre
    assert nombres[1] == otro_titular.nombre

    # Vemos que al lado de cada titular aparece su capital
    capitales = texto_en_hijos_respectivos("class_capital_titular", titulares)
    assert capitales[0] == float_format(titular.capital())
    assert capitales[1] == float_format(otro_titular.capital())

    # Vemos seis cuentas en el menú de cuentas (4 cuentas y 2 subcuentas)
    cuentas = browser.esperar_elementos("class_div_cuenta")
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
    tds_cuenta = browser.esperar_elementos("class_td_cuenta")
    assert "acumulativa" in tds_cuenta[3].get_attribute("class")
    assert "class_td_subcuenta" in tds_cuenta[4].get_attribute("class")
    assert "class_td_subcuenta" in tds_cuenta[5].get_attribute("class")

    # A la derecha de cada una de las cuentas se ve su saldo, el cual
    # corresponde a los movimientos en los que participó
    saldos = texto_en_hijos_respectivos("class_saldo_cuenta", cuentas)
    for i, cta in enumerate([cuenta, cuenta_2, cuenta_3]):
        assert saldos[i] == float_format(sum([
            x.importe_cta_entrada for x in cta.movs() if x.cta_entrada == cta
        ] + [
            x.importe_cta_salida for x in cta.movs() if x.cta_salida == cta
        ]))

    # En la sección de movimientos vemos 7 divisiones de día.
    # Cada una de ellas tiene un título con la fecha y el saldo del día
    # Debajo del título hay una tabla con todos los movimientos del día.
    divs_dia = browser.esperar_elementos("class_div_dia")
    assert len(divs_dia) == 7

    dias = Dia.con_movimientos().reverse()[:7]
    for i, dia in enumerate(dias):
        browser.comparar_dia(divs_dia[i], dia)

    # Al comienzo y al final de la sección de movimientos hay una barra de navegación
    # que nos permite ver días anteriores o posteriores.
    # El link correspondiente a "Días posteriores" está desactivado
    navigator = browser.esperar_elemento("id_div_navigator_init")
    link_posteriores = navigator.esperar_elemento("id_link_anterior_init")
    assert link_posteriores.get_attribute("aria-disabled") == "true"

    # Si cliqueamos en el link que dice "Días anteriores", podemos ver la página con los 7
    # días anteriores.
    primer_dia_pag = divs_dia[-1].esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    navigator.esperar_elemento("id_link_siguiente_init").click()
    divs_dia = browser.esperar_elementos("class_div_dia")
    assert len(divs_dia) == 7
    ultimo_dia_pag = divs_dia[0].esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    assert ultimo_dia_pag < primer_dia_pag

    # Y vemos que en esta página el link correspondiente a "Días posteriores" está activado
    navigator = browser.esperar_elemento("id_div_navigator_init")
    link_posteriores = navigator.esperar_elemento("id_link_anterior_init")
    assert link_posteriores.get_attribute("aria-disabled") == "false"

    # Si cliqueamos en el link que dice "Primeros días", veremos solamente los días anteriores restantes,
    # que pueden ser menos de 7, y el último día de la página será el primer día con movimientos.
    navigator.esperar_elemento("id_link_ultima_init").click()
    divs_dia = browser.esperar_elementos("class_div_dia")
    assert len(divs_dia) == Dia.con_movimientos().count() % 7
    primer_dia_pag = divs_dia[-1].esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    assert str2date(primer_dia_pag) == Dia.con_movimientos().first().fecha

    # Y en esta página, el link correspondiente a "Días anteriores" está desactivado
    navigator = browser.esperar_elemento("id_div_navigator_init")
    link_anteriores = navigator.esperar_elemento("id_link_siguiente_init")
    assert link_anteriores.get_attribute("aria-disabled") == "true"

    # Si desde esta última página cliqueamos en el link que dice "Días posteriores",
    # podemos ver la página con los 7 días posteriores.
    ultimo_dia_pag = divs_dia[0].esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    navigator.esperar_elemento("id_link_anterior_init").click()
    divs_dia = browser.esperar_elementos("class_div_dia")
    primer_dia_pag = divs_dia[-1].esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    assert primer_dia_pag > ultimo_dia_pag
    assert len(divs_dia) == 7

    # Si cliqueamos en el link que dice "Últimos días", volveremos a la primera página, que muestra
    # los últimos días con movimientos
    navigator = browser.esperar_elemento("id_div_navigator_init")
    navigator.esperar_elemento("id_link_primera_init").click()
    divs_dia = browser.esperar_elementos("class_div_dia")
    ultimo_dia_pag = divs_dia[0].esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    assert str2date(ultimo_dia_pag) == Dia.con_movimientos().last().fecha

    # La barra de navegación incluye un número por cada página de 7 días.
    navigator = browser.esperar_elemento("id_div_navigator_init")
    nros_pagina = navigator.esperar_elementos("class_li_pagina_nro")
    assert len(nros_pagina) == (Dia.con_movimientos().count() // 7) + 1

    # El número de página que coincide con la página activa se muestra destacado
    # entre los otros números de página, y su link está desactivado.
    pag_actual = nros_pagina[0]
    assert "active" in pag_actual.get_attribute("class")
    link_pag_actual = pag_actual.esperar_elemento("class_link_pagina", By.CLASS_NAME)
    assert link_pag_actual.get_attribute("aria-disabled") == "true"
    for np in nros_pagina[1:]:
        assert "active" not in np.get_attribute("class")
        link_pag = np.esperar_elemento("class_link_pagina", By.CLASS_NAME)
        assert link_pag.get_attribute("aria-disabled") == "false"

    # Si cliqueamos en un número de página, seremos dirigidos a la página con los
    # 7 (o menos si es la última) días correspondientes.
    nro_pag = nros_pagina[2].text
    nros_pagina[2].click()
    assert urlparse(browser.current_url).query == f"page={nro_pag}"

    # Al final de la barra de navegación por páginas hay un campo en el cual
    # podemos seleccionar un día y seremos dirigidos a la página que contenga
    # ese día. El último movimiento del día de la fecha ingresada aparecerá
    # seleccionado
    browser.ir_a_pag()
    browser.completar_form(boton="id_btn_buscar_dia_init", input_dia_init=fecha)
    fechas = [str2date(x.text[-10:]) for x in browser.esperar_elementos("class_span_fecha_dia")]
    assert fecha in fechas
    dia = Dia.tomar(fecha=fecha)
    mov = dia.movimientos.last()
    browser.assert_url(mov.get_absolute_url() + f"?page={fecha2page(Dia.todes(), fecha)}&redirected=1")

    # Si seleccionamos un día inexistente, seremos llevados a la página que contengan
    # los días aledaños al seleccionado.
    fecha_inexistente = date(2011,4,21)
    browser.completar_form(boton="id_btn_buscar_dia_init", input_dia_init=fecha_inexistente)
    fecha_anterior = Dia.filtro(fecha__lt=fecha_inexistente).last().fecha
    fecha_posterior = Dia.filtro(fecha__gt=fecha_inexistente).first().fecha
    fechas = [str2date(x.text[-10:]) for x in browser.esperar_elementos("class_span_fecha_dia")]
    assert fecha_anterior in fechas
    assert fecha_posterior in fechas
    assert fecha_inexistente not in fechas

    # Lo mismo si seleccionamos un día que no contenga movimientos.
    fecha_sin_movs = fecha_tardia - timedelta(1)
    browser.completar_form(boton="id_btn_buscar_dia_init", input_dia_init=fecha_sin_movs)
    fecha_anterior = Dia.filtro(fecha__lt=fecha_sin_movs).last().fecha
    fechas = [str2date(x.text[-10:]) for x in browser.esperar_elementos("class_span_fecha_dia")]
    assert fecha_sin_movs not in fechas
    assert fecha_anterior in fechas
    assert fecha_tardia in fechas

    # Si buscamos un día con una cuenta seleccionada, sólo se tendrán en cuenta
    # los días en los que haya movimientos de la cuenta seleccionada, y sólo se
    # mostrarán esos movimientos dentro de los días.

    # Lo mismo si lo hacemos con un titular seleccionado.


def test_home_monedas(
        browser, cuenta_con_saldo, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros,
        entrada_anterior, salida, salida_posterior,
        peso, dolar, euro,
        cotizacion_dolar, cotizacion_posterior_dolar, cotizacion_anterior_euro, cotizacion_posterior_euro, request):
    browser.ir_a_pag()
    # En una sección aparte, aparecen todas las monedas
    for moneda, cot in ((peso, None), (dolar, cotizacion_posterior_dolar), (euro, cotizacion_posterior_euro)):
        mon_pag = browser.esperar_elemento(f"id_link_mon_{moneda.sk}")
        assert mon_pag.text == moneda.nombre

        # Al lado de cada una de las monedas, aparece su última cotización para la compra y para la venta
        if cot:
            cot_pag_c = browser.esperar_elemento(f"id_cotizacion_c_{moneda.sk}")
            cot_pag_v = browser.esperar_elemento(f"id_cotizacion_v_{moneda.sk}")
            assert cot_pag_c.text == float_format(cot.importe_compra)
            assert cot_pag_v.text == float_format(cot.importe_venta)

    # Vemos que al lado de cada cuenta aparece una columna por cada moneda, con
    # su saldo expresado en esa moneda. Si la moneda de la columna coincide con
    # la de la cuenta, aparece resaltada.
    for cuenta in (cuenta_con_saldo, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros):
        for moneda in (peso, dolar, euro):
            saldo_mon = browser.esperar_elemento(f"id_saldo_cta_{cuenta.sk}_{moneda.sk}")
            assert saldo_mon.text == float_format(cuenta.saldo(moneda=moneda, compra=False))
            classname = saldo_mon.get_attribute("class")
            if moneda == cuenta.moneda:
                assert "mon_cuenta" in classname
            else:
                assert "mon_cuenta" not in classname

    # Esto también se aplica a las subcuentas de una cuenta acumulativa
    cuenta_acumulativa = request.getfixturevalue('cuenta_acumulativa')
    cuenta_acumulativa_en_dolares = request.getfixturevalue('cuenta_acumulativa_en_dolares')
    browser.ir_a_pag()
    subcuentas = list(cuenta_acumulativa.subcuentas.all() | cuenta_acumulativa_en_dolares.subcuentas.all())
    for cuenta in subcuentas:
        for moneda in (peso, dolar, euro):
            saldo_mon = browser.esperar_elemento(f"id_saldo_cta_{cuenta.sk}_{moneda.sk}")
            assert saldo_mon.text == float_format(cuenta.saldo(moneda=moneda, compra=False))
            classname = saldo_mon.get_attribute("class")
            if moneda == cuenta.moneda:
                assert "mon_cuenta" in classname
            else:
                assert "mon_cuenta" not in classname

    # Si seleccionamos un movimiento, la cotización cambia para mostrar la del día del movimiento seleccionado.
    browser.ir_a_pag(reverse("movimiento", args=[entrada_anterior.pk]))
    for moneda, cot in ((dolar, cotizacion_dolar), (euro, cotizacion_anterior_euro)):
        cot_pag_c = browser.esperar_elemento(f"id_cotizacion_c_{moneda.sk}")
        cot_pag_v = browser.esperar_elemento(f"id_cotizacion_v_{moneda.sk}")
        assert cot_pag_c.text == float_format(cot.importe_compra)
        assert cot_pag_v.text == float_format(cot.importe_venta)

    # Y los saldos de cuenta en distintas monedas aparecen cotizados a la fecha del movimiento seleccionado

    # Si seleccionamos un movimiento de un día en el que no hay cotización, se muestra la última
    # cotización anterior a la fecha del movimiento
    browser.ir_a_pag(reverse("movimiento", args=[salida.pk]))
    for moneda, cot in ((dolar, cotizacion_dolar), (euro, cotizacion_anterior_euro)):
        cot_pag_c = browser.esperar_elemento(f"id_cotizacion_c_{moneda.sk}")
        cot_pag_v = browser.esperar_elemento(f"id_cotizacion_v_{moneda.sk}")
        assert cot_pag_c.text == float_format(cot.importe_compra)
        assert cot_pag_v.text == float_format(cot.importe_venta)

    # Y los saldos de cuenta en distintas monedas aparecen cotizados a la fecha de la última cotización anterior
    # a la del movimiento.

class TestHomeLinks:
    def test_seccion_titulares(self, browser, titular, otro_titular):

        # Cuando cliqueamos en un titular, vamos a la página de ese titular
        browser.ir_a_pag()
        browser.cliquear_en_titular(titular)
        browser.assert_url(titular.get_absolute_url())

        # cuando cliqueamos en el ícono de agregar titular, accedemos a la página para agregar titular nuevo
        browser.verificar_link('titular_nuevo', 'tit_nuevo', querydict={"next": "/"})

        # cuando cliqueamos en el link de editar titular, accedemos a la página de edición de ese titular
        browser.verificar_link(f'tit_mod_{titular.sk}', 'tit_mod', [titular.sk], querydict={"next": "/"})

        # cuando cliqueamos en el link de borrar titular, accedemos a la página de confirmación
        browser.verificar_link(f'tit_elim_{titular.sk}', 'tit_elim', [titular.sk], querydict={"next": "/"})

    def test_seccion_cuentas(self, browser, cuenta, cuenta_2, cuenta_acumulativa):
        subcuenta = cuenta_acumulativa.subcuentas.first()

        # Cuando cliqueamos en una cuenta, vamos a la página de esa cuenta
        browser.ir_a_pag()
        browser.cliquear_en_cuenta(cuenta_2)
        browser.assert_url(cuenta_2.get_absolute_url())

        # Cuando cliqueamos en una subcuenta, vamos a la página de esa subcuenta
        browser.ir_a_pag()
        browser.cliquear_en_cuenta(subcuenta)
        browser.assert_url(subcuenta.get_absolute_url())

        # cuando cliqueamos en el ícono de agregar cuenta, accedemos a la página para agregar cuenta nueva
        browser.verificar_link('cuenta_nueva', 'cta_nueva', querydict={'next': '/'})

        # cuando cliqueamos en el link de editar cuenta, accedemos a la página de edición de esa cuenta
        browser.verificar_link(f'cta_mod_{cuenta.sk}', 'cta_mod', [cuenta.sk], querydict={'next': '/'})
        browser.verificar_link(f'cta_mod_{subcuenta.sk}', 'cta_mod', [subcuenta.sk], querydict={'next': '/'})

        # cuando cliqueamos en el link de borrar cuenta, accedemos a la página de confirmación
        browser.verificar_link(f'cta_elim_{cuenta.sk}', 'cta_elim', [cuenta.sk], querydict={'next': '/'})
        browser.verificar_link(f'cta_elim_{subcuenta.sk}', 'cta_elim', [subcuenta.sk], querydict={'next': '/'})

    def test_seccion_movimientos(self, browser, entrada, salida):

        # cuando cliqueamos en el link de movimiento nuevo, accedemos a la página para agregar movimiento
        browser.verificar_link('mov_nuevo', 'mov_nuevo', querydict={'next': '/'})

        # cuando cliqueamos en el link de editar movimiento, accedemos a la página de edición de ese movimiento
        browser.verificar_link('mod_mov', 'mov_mod', [entrada.pk], querydict={'next': '/'}, criterio=By.CLASS_NAME)

        # cuando cliqueamos en el link de borrar movimiento, accedemos a la página de confirmación
        browser.verificar_link('elim_mov', 'mov_elim', [entrada.pk], querydict={'next': '/'}, criterio=By.CLASS_NAME)

    def test_seccion_monedas(self, browser, peso, dolar):

        # cuando cliqueamos en el link de moneda nueva, accedemos a la página para agregar moneda
        browser.verificar_link('moneda_nueva', 'mon_nueva', querydict={'next': '/'})

        # cuando cliqueamos en el link de editar movimiento, accedemos a la página de edición de ese movimiento
        browser.verificar_link(f'mon_mod_{peso.sk}', 'mon_mod', [peso.sk])

        # cuando cliqueamos en el link de borrar movimiento, accedemos a la página de confirmación
        browser.verificar_link(f'mon_elim_{peso.sk}', 'mon_elim', [peso.sk])
