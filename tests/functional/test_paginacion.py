from datetime import date, timedelta
from urllib.parse import urlparse

import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By

from diario.models import Dia
from diario.utils.utils_saldo import saldo_general_historico
from utils.numeros import float_format
from utils.tiempo import str2date


def test_navegacion_paginas(browser, muchos_dias):
    browser.ir_a_pag(reverse("home"))

    # Al comienzo y al final de la sección de movimientos hay una barra de navegación
    # que nos permite ver días anteriores o posteriores.
    # El link correspondiente a "Días posteriores" está desactivado
    navigator = browser.encontrar_elemento("id_div_navigator_init")
    divs_dia = browser.encontrar_elementos("class_div_dia")
    link_posteriores = navigator.encontrar_elemento("id_link_anterior_init")
    assert link_posteriores.get_attribute("aria-disabled") == "true"

    # Si cliqueamos en el link que dice "Días anteriores", podemos ver la página con los 7
    # días anteriores.
    primer_dia_pag = divs_dia[-1].encontrar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    navigator.encontrar_elemento("id_link_siguiente_init").click()
    divs_dia = browser.encontrar_elementos("class_div_dia")
    assert len(divs_dia) == 7
    ultimo_dia_pag = divs_dia[0].encontrar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    assert ultimo_dia_pag < primer_dia_pag

    # Y vemos que en esta página el link correspondiente a "Días posteriores" está activado
    navigator = browser.encontrar_elemento("id_div_navigator_init")
    link_posteriores = navigator.encontrar_elemento("id_link_anterior_init")
    assert link_posteriores.get_attribute("aria-disabled") == "false"

    # Si cliqueamos en el link que dice "Primeros días", veremos solamente los días anteriores restantes,
    # que pueden ser menos de 7, y el último día de la página será el primer día con movimientos.
    navigator.encontrar_elemento("id_link_ultima_init").click()
    divs_dia = browser.encontrar_elementos("class_div_dia")
    assert len(divs_dia) == Dia.con_movimientos().count() % 7
    primer_dia_pag = divs_dia[-1].encontrar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    assert str2date(primer_dia_pag) == Dia.con_movimientos().first().fecha

    # Y en esta página, el link correspondiente a "Días anteriores" está desactivado
    navigator = browser.encontrar_elemento("id_div_navigator_init")
    link_anteriores = navigator.encontrar_elemento("id_link_siguiente_init")
    assert link_anteriores.get_attribute("aria-disabled") == "true"

    # Si desde esta última página cliqueamos en el link que dice "Días posteriores",
    # podemos ver la página con los 7 días posteriores.
    ultimo_dia_pag = divs_dia[0].encontrar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    navigator.encontrar_elemento("id_link_anterior_init").click()
    divs_dia = browser.encontrar_elementos("class_div_dia")
    primer_dia_pag = divs_dia[-1].encontrar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    assert primer_dia_pag > ultimo_dia_pag
    assert len(divs_dia) == 7

    # Si cliqueamos en el link que dice "Últimos días", volveremos a la primera página, que muestra
    # los últimos días con movimientos
    navigator = browser.encontrar_elemento("id_div_navigator_init")
    navigator.encontrar_elemento("id_link_primera_init").click()
    divs_dia = browser.encontrar_elementos("class_div_dia")
    ultimo_dia_pag = divs_dia[0].encontrar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    assert str2date(ultimo_dia_pag) == Dia.con_movimientos().last().fecha

    # La barra de navegación incluye un número por cada página de 7 días.
    navigator = browser.encontrar_elemento("id_div_navigator_init")
    nros_pagina = navigator.encontrar_elementos("class_li_pagina_nro")
    assert len(nros_pagina) == (Dia.con_movimientos().count() // 7) + 1

    # El número de página que coincide con la página activa se muestra destacado
    # entre los otros números de página, y su link está desactivado.
    pag_actual = nros_pagina[0]
    assert "active" in pag_actual.get_attribute("class")
    link_pag_actual = pag_actual.encontrar_elemento("class_link_pagina", By.CLASS_NAME)
    assert link_pag_actual.get_attribute("aria-disabled") == "true"
    for np in nros_pagina[1:]:
        assert "active" not in np.get_attribute("class")
        link_pag = np.encontrar_elemento("class_link_pagina", By.CLASS_NAME)
        assert link_pag.get_attribute("aria-disabled") == "false"

    # Si cliqueamos en un número de página, seremos dirigidos a la página con los
    # 7 (o menos si es la última) días correspondientes.
    nro_pag = nros_pagina[2].text
    nros_pagina[2].click()
    assert urlparse(browser.current_url).query == f"page={nro_pag}"


@pytest.mark.parametrize("origen, fixt_dias, fecha_en_la_misma_pag", [
    ("home", "muchos_dias", date(2010, 11, 13)),
    ("titular", "muchos_dias_distintos_titulares", date(2010, 11, 14)),
    ("cuenta", "muchos_dias", date(2010, 9, 10))
])
def test_busqueda_fecha(browser, origen, fixt_dias, fecha, fecha_tardia, fecha_en_la_misma_pag, request):
    ente = request.getfixturevalue(origen) if origen != "home" else None
    args = [ente.sk] if ente else []
    request.getfixturevalue(fixt_dias)
    browser.ir_a_pag(reverse(origen, args=args))

    # Al final de la barra de navegación por páginas hay un campo en el cual
    # podemos seleccionar un día y seremos dirigidos a la página que contenga
    # ese día.
    browser.completar_form(boton="id_btn_buscar_dia_init", input_dia_init=fecha)
    fechas = [str2date(x.text[-10:]) for x in browser.encontrar_elementos("class_span_fecha_dia")]
    assert fecha in fechas

    # El último movimiento del día buscado aparece seleccionado
    ultimo_mov_dia = browser.encontrar_dia(fecha).encontrar_elementos("class_row_mov")[-1]
    assert "mov_selected" in ultimo_mov_dia.get_attribute("class")

    # Si buscamos un día que se encuentre en la misma página que un día seleccionado,
    # se deselecciona el día que estaba seleccionado y aparece seleccionado el último
    # movimiento del día buscado
    # fecha_en_la_misma_pagina = date(2010, 11, 13)
    browser.completar_form(boton="id_btn_buscar_dia_init", input_dia_init=fecha_en_la_misma_pag)
    ultimo_mov_dia = browser.encontrar_dia(fecha).encontrar_elementos("class_row_mov")[-1]
    ultimo_mov_nuevo_dia = browser.encontrar_dia(fecha_en_la_misma_pag).encontrar_elementos("class_row_mov")[-1]
    assert "mov_selected" not in ultimo_mov_dia.get_attribute("class")
    assert "mov_selected" in ultimo_mov_nuevo_dia.get_attribute("class")

    # Si buscamos un día inexistente, seremos llevados a la página que contenga
    # el día anterior al seleccionado.
    fecha_inexistente = date(2011, 4, 21)
    browser.completar_form(boton="id_btn_buscar_dia_init", input_dia_init=fecha_inexistente)
    fecha_anterior = Dia.filtro(fecha__lt=fecha_inexistente).last().fecha
    fecha_posterior = Dia.filtro(fecha__gt=fecha_inexistente).first().fecha
    fechas = [str2date(x.text[-10:]) for x in browser.encontrar_elementos("class_span_fecha_dia")]
    assert fecha_anterior in fechas
    assert fecha_posterior in fechas
    assert fecha_inexistente not in fechas

    # Lo mismo si buscamos un día que no contenga movimientos.
    fecha_sin_movs = fecha_tardia - timedelta(1)
    browser.completar_form(boton="id_btn_buscar_dia_init", input_dia_init=fecha_sin_movs)
    fecha_anterior = Dia.filtro(fecha__lt=fecha_sin_movs).last().fecha
    fechas = [str2date(x.text[-10:]) for x in browser.encontrar_elementos("class_span_fecha_dia")]
    assert fecha_sin_movs not in fechas
    assert fecha_anterior in fechas
    assert fecha_tardia in fechas

    # Si buscamos un día con una cuenta seleccionada, sólo se tendrán en cuenta
    # los días en los que haya movimientos de la cuenta seleccionada, y sólo se
    # mostrarán esos movimientos dentro de los días.

    # Lo mismo si lo hacemos con un titular seleccionado.


@pytest.mark.parametrize("page", ["", "?page=2"])
def test_saldo_diario_en_paginas(browser, mas_de_7_dias, page):
    # Si vamos a una página posterior a la primera, cada día muestra el saldo
    # general diario
    browser.ir_a_pag(reverse("home") + page)
    dias_pag = browser.encontrar_elementos("class_titulo_dia")
    for dia_pag in dias_pag:
        fecha = str2date(dia_pag.encontrar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:])
        dia = Dia.tomar(fecha=fecha)
        saldo_mostrado = dia_pag.encontrar_elemento("class_span_saldo_dia", By.CLASS_NAME).text
        saldo_real = saldo_general_historico(dia=dia)
        assert saldo_mostrado == float_format(saldo_real)
        print(fecha, saldo_mostrado, "=", saldo_real)
