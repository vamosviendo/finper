from datetime import date

import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By

from diario.models import CuentaAcumulativa, CuentaInteractiva, Dia, Movimiento
from pytests.functional.helpers import texto_en_hijos_respectivos
from utils.numeros import float_format
from utils.tiempo import str2date


@pytest.fixture
def subcuenta_otro_titular(cuenta_de_dos_titulares: CuentaAcumulativa) -> CuentaInteractiva:
    return cuenta_de_dos_titulares.subcuentas.first()


@pytest.fixture
def subcuenta_titular_gordo(cuenta_de_dos_titulares: CuentaAcumulativa) -> CuentaInteractiva:
    return cuenta_de_dos_titulares.subcuentas.last()


@pytest.fixture
def entrada_subcuenta(subcuenta_otro_titular: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto="Entrada en subcuenta otro titular",
        importe=33,
        cta_entrada=subcuenta_otro_titular,
        fecha=fecha,
    )


@pytest.fixture
def entrada_posterior_subcuenta(subcuenta_otro_titular: CuentaInteractiva, fecha_posterior: date) -> Movimiento:
    return Movimiento.crear(
        concepto="Entrada posterior en subcuenta otro titular",
        importe=78,
        cta_entrada=subcuenta_otro_titular,
        fecha=fecha_posterior,
    )


def test_detalle_de_cuenta_interactiva(
        browser,
        titular, otro_titular, titular_gordo,
        cuenta, entrada, salida, salida_posterior, entrada_otra_cuenta, salida_tardia_tercera_cuenta,
        mas_de_7_dias):

    # Vamos a la página de inicio
    browser.ir_a_pag()

    # Cliqueamos en el nombre de una cuenta interactiva
    browser.cliquear_en_cuenta(cuenta)

    # Vemos el nombre de la cuenta encabezando la página, con su fecha de
    # creación y su saldo
    browser.comparar_cuenta(cuenta)

    # Y vemos que en la sección de titulares aparece el titular de la cuenta
    divs_titular = browser.esperar_elementos("class_div_titular")
    assert len(divs_titular) == 1
    nombres = texto_en_hijos_respectivos("class_div_nombre_titular", divs_titular)
    assert nombres[0] == cuenta.titular.nombre

    # Y vemos que no aparecen cuentas en la sección de cuentas
    assert browser.esperar_elementos('class_link_cuenta', fail=False) == []

    # Y vemos que sólo los días en los que hay movimientos en los que interviene
    # la cuenta aparecen en la sección de movimientos
    divs_dia = browser.esperar_elementos("class_div_dia")
    assert len(divs_dia) == 7
    fechas_dia = texto_en_hijos_respectivos("class_span_fecha_dia", divs_dia)
    assert fechas_dia == [x.str_dia_semana() for x in cuenta.dias().reverse()[:7]]

    # Y vemos que solo los movimientos en los que interviene la cuenta aparecen
    # dentro de cada día
    for dia_pag in divs_dia:
        fecha_pag = dia_pag.esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text
        browser.comparar_movimientos_de_fecha_de(
            cuenta,
            fecha=str2date(fecha_pag.split()[1]),
            container=dia_pag
        )

    assert set(cuenta.movs()) != set(Movimiento.todes())

    # Cuando cliqueamos en el ícono de agregar cuenta, accedemos a la página
    # de dividir cuenta en subcuentas
    browser.esperar_elemento("id_link_cuenta_nueva").click()
    browser.assert_url(reverse('cta_div', args=[cuenta.slug]))

    # Cuando cliqueamos en un movimiento, sólo se muestran los días con
    # movimientos relacionados con la cuenta, y en esos días se muestran
    # sólo los movimientos relacionados con la cuenta, con el movimiento
    # cliqueado resaltado.
    browser.ir_a_pag(reverse('cuenta', args=[cuenta.slug]))
    dias_pag = browser.serializar_dias_pagina()

    dias_pag[1]["movimientos"][0]["webelement"].esperar_elemento("class_link_movimiento", By.CLASS_NAME).click()

    dias_pag_nueva = browser.comparar_dias_de(cuenta)
    assert "mov_selected" in dias_pag_nueva[1]["movimientos"][0]["webelement"].get_attribute("class")

    # Y vemos que en el saldo de la página aparece el saldo histórico
    # de la cuenta al momento del movimiento
    nombre_cuenta = browser.esperar_elemento(
        'id_titulo_saldo_gral'
    ).text.strip()
    movimiento = cuenta.movs().get(dia=Dia.tomar(fecha=dias_pag[1]["fecha"][-10:]), orden_dia=0)

    assert nombre_cuenta == (f"{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion}) "
                              f"en movimiento {movimiento.orden_dia} "
                              f"del {movimiento.fecha} ({movimiento.concepto}):")
    browser.comparar_saldo_historico_de(cuenta, movimiento)

    # Y al lado del titular de la cuenta (que es el único que se ve) aparece
    # su capital histórico al momento del movimiento
    divs_titular = browser.esperar_elementos("class_div_titular")
    assert len(divs_titular) == 1
    nombres = texto_en_hijos_respectivos("class_div_nombre_titular", divs_titular)
    assert nombres[0] == cuenta.titular.nombre
    capitales = texto_en_hijos_respectivos("class_capital_titular", divs_titular)
    assert capitales[0] == float_format(titular.capital_historico(movimiento))


def test_detalle_de_cuenta_acumulativa(
        browser, entrada_otra_cuenta, cuenta_de_dos_titulares,
        credito_entre_subcuentas, entrada_subcuenta, entrada_posterior_subcuenta):
    sc1, sc2 = cuenta_de_dos_titulares.subcuentas.all()

    # Dada una cuenta acumulativa cuyas subcuentas acumulan más de 7 días
    # con movimientos
    Movimiento.crear(fecha=date(2021, 2, 3), concepto="mov", cta_entrada=sc1, importe=25)
    Movimiento.crear(fecha=date(2021, 5, 8), concepto="mov", cta_entrada=sc2, importe=24)
    Movimiento.crear(fecha=date(2021, 3, 9), concepto="mov", cta_entrada=sc2, importe=23)
    Movimiento.crear(fecha=date(2021, 6, 2), concepto="mov", cta_entrada=sc1, importe=22)
    Movimiento.crear(fecha=date(2021, 6, 1), concepto="mov", cta_entrada=sc1, importe=21)
    Movimiento.crear(fecha=date(2021, 10, 3), concepto="mov", cta_entrada=sc2, importe=20)

    # Vamos a la página principal y cliqueamos en el nombre de una cuenta
    # acumulativa
    browser.ir_a_pag()
    browser.cliquear_en_cuenta(cuenta_de_dos_titulares)

    # Vemos el nombre de la cuenta encabezando la página
    browser.comparar_cuenta(cuenta_de_dos_titulares)

    # Y vemos que al lado del nombre aparece el saldo de la cuenta
    browser.comparar_saldo_de(cuenta_de_dos_titulares)

    # Vemos las subcuentas de la cuenta acumulativa, los titulares de las
    # subcuentas y los movimientos relacionados con ella o sus subcuentas
    browser.comparar_subcuentas_de(cuenta_de_dos_titulares)
    browser.comparar_titulares_de(cuenta_de_dos_titulares)
    browser.comparar_dias_de(cuenta_de_dos_titulares)

    # Cuando cliqueamos en el ícono de agregar cuenta, accedemos a la página
    # de agregar subcuenta
    browser.esperar_elemento("id_link_cuenta_nueva").click()
    browser.assert_url(reverse(
        'cta_agregar_subc',
        args=[cuenta_de_dos_titulares.slug])
    )

    # Volvemos a la página de la cuenta y cliqueamos en el nombre de la
    # primera subcuenta
    primera_subcuenta = cuenta_de_dos_titulares.subcuentas.first()
    browser.ir_a_pag(
        reverse('cuenta', args=[cuenta_de_dos_titulares.slug])
    )
    browser.cliquear_en_cuenta(primera_subcuenta)

    # Vemos el nombre de la cuenta encabezando la página
    browser.comparar_cuenta(primera_subcuenta)

    # Y vemos que al lado del nombre aparece el saldo de la cuenta
    browser.comparar_saldo_de(primera_subcuenta)

    # Y vemos que antes del nombre y saldo de la cuenta aparece en tipografía
    # menos destacada el nombre y saldo de su cuenta madre
    saldo_cta_madre = browser.esperar_elemento("class_div_saldo_ancestro", By.CLASS_NAME).text
    assert \
        saldo_cta_madre == \
        f"Saldo de cuenta madre {cuenta_de_dos_titulares.nombre}: " \
        f"{float_format(cuenta_de_dos_titulares.saldo())}"

    # Y vemos que luego del nombre y saldo de la cuenta aprece en tipografía
    # menos destacada el nombre y saldo de sus hermanas de cuenta
    saldos_ctas_hermanas = [
        x.text for x in browser.esperar_elementos("class_div_saldo_hermana")
    ]
    assert len(saldos_ctas_hermanas) == primera_subcuenta.hermanas().count()
    for index, hermana in enumerate(primera_subcuenta.hermanas()):
        assert \
            saldos_ctas_hermanas[index] == \
            f"Saldo de cuenta hermana {hermana.nombre}: " \
            f"{float_format(hermana.saldo())}"

    # Y vemos el titular de la primera subcuenta y los movimientos en los que
    # interviene

    browser.comparar_titulares_de(primera_subcuenta)
    browser.comparar_dias_de(primera_subcuenta)

    # Volvemos a la página de la cuenta acumulativa y cliqueamos en el nombre
    # de la segunda subcuenta
    browser.ir_a_pag(
        reverse('cuenta', args=[cuenta_de_dos_titulares.slug])
    )
    segunda_subcuenta = cuenta_de_dos_titulares.subcuentas.last()
    browser.cliquear_en_cuenta(segunda_subcuenta)

    # Vemos el titular de la segunda subcuenta y los movimientos en los que
    # interviene
    browser.comparar_titulares_de(segunda_subcuenta)
    browser.comparar_dias_de(segunda_subcuenta)

    # Volvemos a la página de la cuenta acumulativa y cliqueamos en un
    # movimiento
    browser.ir_a_pag(
        reverse('cuenta', args=[cuenta_de_dos_titulares.slug])
    )
    links_movimiento = browser.esperar_elementos("class_link_movimiento")
    links_movimiento[1].click()

    # Vemos que en la sección de movimientos aparecen los movimientos de la
    # cuenta o sus subcuentas, con el movimiento cliqueado resaltado
    browser.comparar_dias_de(cuenta_de_dos_titulares)
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movimientos[1].get_attribute("class")

    # Y vemos que en el saldo general de la página aparece el saldo histórico
    # de la cuenta acumulativa al momento del movimiento
    movimiento = cuenta_de_dos_titulares.movs().order_by(
        '-dia', 'orden_dia')[1]
    assert movimiento.concepto == movimientos[1].esperar_elemento(
        "class_td_concepto",
        By.CLASS_NAME
    ).text
    assert \
        cuenta_de_dos_titulares.saldo() != \
        cuenta_de_dos_titulares.saldo_en_mov(movimiento)
    assert \
        browser.esperar_elemento("id_importe_saldo_gral").text == \
        float_format(cuenta_de_dos_titulares.saldo_en_mov(movimiento))

    # Y vemos que al lado de cada una de las subcuentas aparece el saldo
    # histórico de la subcuenta al momento del movimiento
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_saldo_cuenta")]
    for index, cta in enumerate(cuenta_de_dos_titulares.subcuentas.all()):
        assert saldos_historicos[index] == float_format(cta.saldo_en_mov(movimiento))

    # Y vemos que al lado de cada uno de los titulares aparece el capital
    # histórico del titular al momento del movimiento
    capitales_historicos = [
        x.text for x in browser.esperar_elementos("class_capital_titular")]
    for index, titular in enumerate(cuenta_de_dos_titulares.titulares):
        assert capitales_historicos[index] == float_format(titular.capital_historico(movimiento))


@pytest.fixture
def subsubcuenta_1_con_movimientos(
        subsubcuenta: CuentaInteractiva,
        dia: Dia, dia_posterior: Dia, dia_tardio: Dia) -> CuentaInteractiva:
    Movimiento.crear(
        concepto='entrada en subsubcuenta 1',
        importe=34,
        cta_entrada=subsubcuenta,
        dia=dia,
    )
    Movimiento.crear(
        concepto='entrada posterior en subsubcuenta 2',
        importe=242,
        cta_entrada=subsubcuenta,
        dia=dia_posterior,
    )
    Movimiento.crear(
        concepto='salida de subsubcuenta 1',
        importe=49,
        cta_salida=subsubcuenta,
        dia=dia_tardio,
    )

    return subsubcuenta


@pytest.fixture
def subsubcuenta_2_con_movimientos(
        subsubcuenta_2: CuentaInteractiva,
        dia: Dia, dia_posterior: Dia) -> CuentaInteractiva:
    Movimiento.crear(
        concepto='entrada en subsubcuenta 2',
        importe=25,
        cta_entrada=subsubcuenta_2,
        dia=dia,
    )
    Movimiento.crear(
        concepto='entrada posterior en subsubcuenta 2',
        importe=158,
        cta_entrada=subsubcuenta_2,
        dia=dia_posterior,
    )
    return subsubcuenta_2


@pytest.fixture
def subsubcuenta_3_con_movimientos(
        subsubcuenta_2: CuentaInteractiva,
        dia: Dia, dia_tardio: Dia) -> CuentaInteractiva:
    ssc3 = subsubcuenta_2.cta_madre.agregar_subcuenta(
        nombre='subsubcuenta 3',
        slug='ssc3',
        titular=subsubcuenta_2.titular,
        fecha=dia.fecha
    )

    Movimiento.crear(
        concepto='entrada en subsubcuenta 3',
        importe=28,
        cta_entrada=ssc3,
        dia=dia,
    )
    Movimiento.crear(
        concepto='entrada tardía en subsubcuenta 3',
        importe=281,
        cta_entrada=ssc3,
        dia=dia_tardio,
    )

    return ssc3


@pytest.mark.xfail
def test_detalle_de_subcuenta(
        browser, cuenta_acumulativa, subsubcuenta_1_con_movimientos, subsubcuenta_2_con_movimientos,
        subsubcuenta_3_con_movimientos):
    # TODO: Este test a veces falla. Habría que probar qué pasa actualizando Selenium.
    #       Me parece que es una cuestión de esperas, pero no podría asegurarlo.
    #       Pasa cuando se lo ejecuta solo. Falla cuando se lo ejecuta junto con los otros tests.
    #       No quiero perder tiempo ahora averiguando cuál es el problema.
    # Dadas dos subcuentas de una cuenta acumulativa
    # Y una de esas subcuentas a la vez dividida en tres subcuentas
    # Y algunos movimientos de las tres subcuentas

    # Cuando vamos a la página de la primera subcuenta de la subcuenta dividida
    browser.ir_a_pag(reverse("cuenta", args=[subsubcuenta_1_con_movimientos.slug]))

    # Vemos el nombre de la cuenta encabezando la página
    # Y vemos que al lado del nombre aparece el saldo de la sub-subcuenta
    browser.comparar_cuenta(subsubcuenta_1_con_movimientos)

    # Y vemos que antes del nombre y saldo de la cuenta aparece el nombre y saldo de sus cuentas ancestro
    saldos_ancestro = [
        x.text for x in browser.esperar_elementos("class_div_saldo_ancestro")
    ]
    assert \
        saldos_ancestro == [
            f"Saldo de cuenta madre {cuenta_acumulativa.nombre}: "
            f"{float_format(cuenta_acumulativa.saldo())}",
            f"Saldo de cuenta madre {subsubcuenta_1_con_movimientos.cta_madre.nombre}: "
            f"{float_format(subsubcuenta_1_con_movimientos.cta_madre.saldo())}",
        ]

    # Y vemos que luego del nombre y saldo de la cuenta aparece el nombre y saldo de sus cuentas hermanas
    saldos_hermana = [
        x.text for x in browser.esperar_elementos("class_div_saldo_hermana")
    ]
    assert \
        saldos_hermana == [
            f"Saldo de cuenta hermana subsubcuenta 2: {float_format(subsubcuenta_2_con_movimientos.saldo())}",
            f"Saldo de cuenta hermana subsubcuenta 3: {float_format(subsubcuenta_3_con_movimientos.saldo())}",
        ]

    # Cliqueamos en un movimiento.
    browser.ir_a_pag(reverse("cuenta_movimiento", args=[subsubcuenta_1_con_movimientos.slug, 7]))

    # Vemos que en la sección de movimientos aparecen los días en los que hay movimientos
    # de la cuenta, con el movimiento cliqueado resaltado
    browser.comparar_dias_de(subsubcuenta_1_con_movimientos)
    row_mov = browser.esperar_elementos("class_div_dia")[1].esperar_elemento("class_row_mov", By.CLASS_NAME)
    assert "mov_selected" in row_mov.get_attribute("class")

    # Y vemos que en el saldo general de la página aparece el saldo histórico
    # de la cuenta al momento del movimiento.
    movimiento = Movimiento.tomar(pk=7)
    assert \
        browser.esperar_elemento("id_importe_saldo_gral").text == \
        float_format(subsubcuenta_1_con_movimientos.saldo_en_mov(movimiento))

    # Y vemos que al lado de cada una de las cuentas ancestro aparece el saldo
    # histórico de la cuenta al momento del movimiento
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_div_saldo_ancestro")]
    for index, cta in enumerate(reversed(subsubcuenta_1_con_movimientos.ancestros())):
        assert saldos_historicos[index].replace(
            f'Saldo de cuenta madre {cta.nombre}: ', ''
        ) == float_format(cta.saldo_en_mov(movimiento))

    # Y vemos que al lado de cada una de las subcuentas hermanas aparece el
    # saldo histórico de la subcuenta al momento del movimiento
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_div_saldo_hermana")]
    for index, cta in enumerate(subsubcuenta_1_con_movimientos.hermanas()):
        assert saldos_historicos[index].replace(
            f'Saldo de cuenta hermana {cta.nombre}: ', ''
        ) == float_format(cta.saldo_en_mov(movimiento))
