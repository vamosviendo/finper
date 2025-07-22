from datetime import date
from urllib.parse import urlparse

import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By

from diario.models import CuentaAcumulativa, CuentaInteractiva, Dia, Movimiento
from pytests.functional.helpers import texto_en_hijos_respectivos
from utils.helpers_tests import fecha2page
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
        sk='ssc3',
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
    # la cuenta aparecen en la sección de movimientos, mostrando sólo los movimientos
    # en los que interviene la cuenta.
    browser.comparar_dias_de(cuenta)

    assert set(cuenta.movs()) != set(Movimiento.todes())

    # Cuando cliqueamos en el ícono de agregar cuenta, accedemos a la página
    # de dividir cuenta en subcuentas.
    # En el url de la página se incluye la información necesaria para regresar
    # a la página actual luego de agregar la subcuenta
    path = urlparse(browser.current_url).path
    browser.esperar_elemento("id_link_cuenta_nueva").click()
    browser.assert_url(reverse('cta_div', args=[cuenta.sk]) + f"?next={path}")

    # Cuando cliqueamos en un movimiento, sólo se muestran los días con
    # movimientos relacionados con la cuenta, y en esos días se muestran
    # sólo los movimientos relacionados con la cuenta, con el movimiento
    # cliqueado resaltado.
    browser.ir_a_pag(cuenta.get_absolute_url())
    dias_pag = browser.esperar_elementos("class_div_dia")

    fecha_dia = dias_pag[1].esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]
    dias_pag[1].esperar_elementos("class_row_mov")[0].esperar_elemento("class_link_movimiento", By.CLASS_NAME).click()

    dias_pag_nueva = browser.comparar_dias_de(cuenta)
    assert "mov_selected" in dias_pag_nueva[1].esperar_elementos("class_row_mov")[0].get_attribute("class")

    # Y vemos que en el saldo de la página aparece el saldo histórico
    # de la cuenta al momento del movimiento
    nombre_cuenta = browser.esperar_elemento(
        'id_titulo_saldo_gral'
    ).text.strip()
    movimiento = cuenta.movs().filter(dia=Dia.tomar(fecha=fecha_dia)).first()

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
    assert capitales[0] == float_format(titular.capital(movimiento))


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
    browser.assert_url(
        reverse(
            'cta_agregar_subc',
            args=[cuenta_de_dos_titulares.sk]
        ) + f"?next={cuenta_de_dos_titulares.get_absolute_url()}"
    )

    # Volvemos a la página de la cuenta y cliqueamos en el nombre de la
    # primera subcuenta
    primera_subcuenta = cuenta_de_dos_titulares.subcuentas.first()
    browser.ir_a_pag(cuenta_de_dos_titulares.get_absolute_url())
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
    browser.ir_a_pag(cuenta_de_dos_titulares.get_absolute_url())
    segunda_subcuenta = cuenta_de_dos_titulares.subcuentas.last()
    browser.cliquear_en_cuenta(segunda_subcuenta)

    # Vemos el titular de la segunda subcuenta y los movimientos en los que
    # interviene
    browser.comparar_titulares_de(segunda_subcuenta)
    browser.comparar_dias_de(segunda_subcuenta)

    # Volvemos a la página de la cuenta acumulativa y cliqueamos en un
    # movimiento
    browser.ir_a_pag(cuenta_de_dos_titulares.get_absolute_url())
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
        cuenta_de_dos_titulares.saldo(movimiento)
    assert \
        browser.esperar_elemento("id_importe_saldo_gral").text == \
        float_format(cuenta_de_dos_titulares.saldo(movimiento))

    # Y vemos que al lado de cada una de las subcuentas aparece el saldo
    # histórico de la subcuenta al momento del movimiento
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_saldo_cuenta")]
    for index, cta in enumerate(cuenta_de_dos_titulares.subcuentas.all()):
        assert saldos_historicos[index] == float_format(cta.saldo(movimiento))

    # Y vemos que al lado de cada uno de los titulares aparece el capital
    # histórico del titular al momento del movimiento
    capitales_historicos = [
        x.text for x in browser.esperar_elementos("class_capital_titular")]
    for index, titular in enumerate(cuenta_de_dos_titulares.titulares):
        assert capitales_historicos[index] == float_format(titular.capital(movimiento))


def test_detalle_de_subcuenta(
        browser, cuenta_acumulativa, subsubcuenta_1_con_movimientos, subsubcuenta_2_con_movimientos,
        subsubcuenta_3_con_movimientos):
    # Dadas dos subcuentas de una cuenta acumulativa
    # Y una de esas subcuentas a la vez dividida en tres subcuentas
    # Y algunos movimientos de las tres subcuentas

    # Cuando vamos a la página de la primera subcuenta de la subcuenta dividida
    browser.ir_a_pag(subsubcuenta_1_con_movimientos.get_absolute_url())

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

    # Cliqueamos en un movimiento
    movimiento = Movimiento.tomar(fecha=date(2011, 5, 1), orden_dia=0)
    browser.ir_a_pag(subsubcuenta_1_con_movimientos.get_url_with_mov(movimiento))

    # Vemos que en la sección de movimientos aparecen los días en los que hay movimientos
    # de la cuenta, con el movimiento cliqueado resaltado
    browser.comparar_dias_de(subsubcuenta_1_con_movimientos)
    row_mov = browser.esperar_elementos("class_div_dia")[1].esperar_elemento("class_row_mov", By.CLASS_NAME)
    assert "mov_selected" in row_mov.get_attribute("class")

    # Y vemos que en el saldo general de la página aparece el saldo histórico
    # de la cuenta al momento del movimiento.
    assert \
        browser.esperar_elemento("id_importe_saldo_gral").text == \
        float_format(subsubcuenta_1_con_movimientos.saldo(movimiento))

    # Y vemos que al lado de cada una de las cuentas ancestro aparece el saldo
    # histórico de la cuenta al momento del movimiento
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_div_saldo_ancestro")]
    for index, cta in enumerate(reversed(subsubcuenta_1_con_movimientos.ancestros())):
        assert saldos_historicos[index] == f"Saldo de cuenta madre {cta.nombre}: {float_format(cta.saldo(movimiento))}"

    # Y vemos que al lado de cada una de las subcuentas hermanas aparece el
    # saldo histórico de la subcuenta al momento del movimiento
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_div_saldo_hermana")]
    for index, cta in enumerate(subsubcuenta_1_con_movimientos.hermanas()):
        assert saldos_historicos[index] == f"Saldo de cuenta hermana {cta.nombre}: {float_format(cta.saldo(movimiento))}"


def test_busqueda_de_fecha_en_detalle_de_cuenta(browser, cuenta, cuenta_2, muchos_dias):
    # Vamos a la página de detalle de una cuenta
    browser.ir_a_pag(cuenta.get_absolute_url())

    # Si completamos el form de búsqueda con una fecha determinada, somos llevados
    # a la página que contiene esa fecha teniendo en cuenta solamente los días
    # que contengan movimientos en los que interviene la cuenta.

    dia = cuenta.dias()[6]  # Dia con sólo movimientos de la cuenta anterior a los últimos 7
    dia2 = cuenta.dias()[7]  # Dia adyacente a dia (debería aparecer en la misma página)
    # Dia adyacente a dia sin movimientos de la cuenta (el día no debería aparecer en la página):
    dias_no_cuenta = [x for x in Dia.todes() if x not in cuenta.dias()]
    dia_no_cuenta = dias_no_cuenta[7]
    dia_anterior_cuenta = cuenta.dias().filter(fecha__lt=dia_no_cuenta.fecha).last()
    mov_cuenta_dia_anterior = cuenta.movs().filter(dia=dia_anterior_cuenta).last()
    # Movimiento de dia2 pero de otra cuenta (no debería aparecer en día2)
    mov_cuenta_dia2 = Movimiento.tomar(dia=dia2)
    mov_no_cuenta_dia2 = Movimiento.crear(
        concepto='Movimiento de otra cuenta', importe=47,
        cta_entrada=cuenta_2, dia=dia2
    )

    browser.completar_form(boton="id_btn_buscar_dia_init", input_dia_init=dia.fecha)

    # El url de la página de destino corresponde a la cuenta e incluye un querystring
    # con la fecha ingresada. El último movimiento del titular del día de la fecha
    # aparece seleccionado.
    mov = dia.movimientos.last()
    browser.assert_url(cuenta.get_url_with_mov(mov) + f"?page={fecha2page(cuenta.dias(), dia.fecha)}")

    # En la página se muestran solamente los días con movimientos de la cuenta.
    # No se muestran los demás días.
    fechas_pag = [str2date(x.text[-10:]) for x in browser.esperar_elementos("class_span_fecha_dia")]
    assert dia.fecha in fechas_pag
    assert dia_no_cuenta.fecha not in fechas_pag

    # Si en alguno de los días que se muestran hay movimientos que no involucren
    # a la cuenta, esos movimientos no se muestran.
    assert dia2.fecha in fechas_pag, "Justo ese movimiento no se encuentra entre las fechas de la página. Probar con otro"
    dia_pag = next(
        x for x in browser.esperar_elementos("class_div_dia")
        if str2date(x.esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text[-10:]) == dia2.fecha
    )
    ordenes_dia_movs_dia = [
        x.esperar_elemento("class_td_orden_dia", By.CLASS_NAME).text
        for x in dia_pag.esperar_elementos("class_row_mov")
    ]
    assert str(mov_cuenta_dia2.orden_dia) in ordenes_dia_movs_dia
    assert str(mov_no_cuenta_dia2.orden_dia) not in ordenes_dia_movs_dia

    # Si la fecha corresponde a un día sin movimientos del titular, se muestra
    # la página que incluye al día anterior con movimientos del titular, con
    # el último movimiento del día seleccionado.
    browser.ir_a_pag(cuenta.get_absolute_url())
    browser.completar_form(boton="id_btn_buscar_dia_init", input_dia_init=dia_no_cuenta.fecha)
    browser.assert_url(
        cuenta.get_url_with_mov(mov_cuenta_dia_anterior) +
        f"?page={fecha2page(cuenta.dias(), dia_anterior_cuenta.fecha)}"
    )
