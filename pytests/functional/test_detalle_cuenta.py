import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By

from diario.models import CuentaAcumulativa, CuentaInteractiva, Movimiento
from pytests.functional.helpers import texto_en_hijos_respectivos
from utils.numeros import float_format


@pytest.fixture
def credito_entre_subcuentas(cuenta_de_dos_titulares: CuentaAcumulativa) -> Movimiento:
    scot, sctg = cuenta_de_dos_titulares.subcuentas.all()
    return Movimiento.crear('Crédito entre subcuentas', 50, scot, sctg)


@pytest.fixture
def subcuenta_otro_titular(cuenta_de_dos_titulares: CuentaAcumulativa) -> CuentaInteractiva:
    return cuenta_de_dos_titulares.subcuentas.first()


@pytest.fixture
def subcuenta_titular_gordo(cuenta_de_dos_titulares: CuentaAcumulativa) -> CuentaInteractiva:
    return cuenta_de_dos_titulares.subcuentas.last()


@pytest.fixture
def entrada_subcuenta(subcuenta_otro_titular: CuentaInteractiva) -> Movimiento:
    return Movimiento.crear(
        concepto="Entrada en subcuenta otro titular",
        importe=33,
        cta_entrada=subcuenta_otro_titular
    )


def test_detalle_de_cuenta_interactiva(
        browser,
        titular, otro_titular, titular_gordo,
        cuenta, entrada, salida, salida_posterior, entrada_otra_cuenta):
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

    # Y vemos que solo los movimientos en los que interviene la cuenta aparecen
    # en la sección de movimientos
    browser.comparar_movimientos_de(cuenta)
    assert set(cuenta.movs()) != set(Movimiento.todes())

    # Cuando cliqueamos en el ícono de agregar cuenta, accedemos a la página
    # de dividir cuenta en subcuentas
    browser.esperar_elemento("id_link_cuenta_nueva").click()
    browser.assert_url(reverse('cta_div', args=[cuenta.slug]))

    # Cuando cliqueamos en un movimiento, solo se muestran los movimientos
    # relacionados con la cuenta, con el movimiento cliqueado resaltado
    browser.ir_a_pag(reverse('cuenta', args=[cuenta.slug]))
    links_movimiento = browser.esperar_elementos("class_link_movimiento")
    links_movimiento[1].click()
    browser.comparar_movimientos_de(cuenta)
    assert set(cuenta.movs()) != set(Movimiento.todes())
    movs_pagina = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movs_pagina[1].get_attribute("class")

    # Y vemos que en el saldo de la página aparece el saldo histórico
    # de la cuenta al momento del movimiento
    nombre_cuenta = browser.esperar_elemento(
        'id_titulo_saldo_gral'
    ).text.strip()
    movimiento = cuenta.movs()[1]

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
        credito_entre_subcuentas, entrada_subcuenta):

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
    browser.comparar_movimientos_de(cuenta_de_dos_titulares)

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
        f"{float_format(cuenta_de_dos_titulares.saldo)}"

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
            f"{float_format(hermana.saldo)}"

    # Y vemos el titular de la primera subcuenta y los movimientos en los que
    # interviene

    browser.comparar_titulares_de(primera_subcuenta)
    browser.comparar_movimientos_de(primera_subcuenta)

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
    browser.comparar_movimientos_de(segunda_subcuenta)

    # Volvemos a la página de la cuenta acumulativa y cliqueamos en un
    # movimiento
    browser.ir_a_pag(
        reverse('cuenta', args=[cuenta_de_dos_titulares.slug])
    )
    links_movimiento = browser.esperar_elementos("class_link_movimiento")
    links_movimiento[1].click()

    # Vemos que en la sección de movimientos aparecen los movimientos de la
    # cuenta o sus subcuentas, con el movimiento cliqueado resaltado
    browser.comparar_movimientos_de(cuenta_de_dos_titulares)
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movimientos[1].get_attribute("class")

    # Y vemos que en el saldo general de la página aparece el saldo histórico
    # de la cuenta acumulativa al momento del movimiento
    movimiento = cuenta_de_dos_titulares.movs().order_by(
        '-fecha', '-orden_dia')[1]
    assert movimiento.concepto == movimientos[1].find_element_by_class_name(
        "class_td_concepto").text
    assert \
        cuenta_de_dos_titulares.saldo != \
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


def test_detalle_de_subcuenta(browser, titular, cuenta_de_dos_titulares):
    # Dadas dos subcuentas de una cuenta acumulativa
    scot, sctg = cuenta_de_dos_titulares.subcuentas.all()

    # Y una de esas subcuentas a la vez dividida en tres subcuentas
    scot_pk = scot.pk
    ssc1, ssc2, ssc3 = scot.dividir_entre(
        {
            'nombre': 'subsubuenta 1',
            'slug': 'ssc1',
            'saldo': 10,
            'titular': scot.titular
        },
        {
            'nombre': 'subsubcuenta 2',
            'slug': 'ssc2',
            'saldo': 20,
            'titular': sctg.titular
        },
        {
            'nombre': 'subsubcuenta 3',
            'slug': 'ssc3',
            'titular': titular
        },
    )

    # Y algunos movimientos de las tres sub-subcuentas
    Movimiento.crear(
        concepto='entrada en subsubcuenta 1',
        importe=34,
        cta_entrada=ssc1,
    )
    Movimiento.crear(
        concepto='entrada en subsubcuenta 2',
        importe=25,
        cta_entrada=ssc2,
    )
    Movimiento.crear(
        concepto='entrada en subsubcuenta 3',
        importe=28,
        cta_entrada=ssc3,
    )
    Movimiento.crear(
        concepto='otra entrada en subsubcuenta 1',
        importe=158,
        cta_entrada=ssc1,
    )
    Movimiento.crear(
        concepto='otra entrada en subsubcuenta 2',
        importe=242,
        cta_entrada=ssc2,
    )
    Movimiento.crear(
        concepto='otra entrada en subsubcuenta 3',
        importe=281,
        cta_entrada=ssc3,
    )
    Movimiento.crear(
        concepto='salida de subsubcuenta 1',
        importe=49,
        cta_salida=ssc1,
    )
    scot_acumulativa = CuentaAcumulativa.tomar(pk=scot_pk)

    # Cuando vamos a la página de la primera sub-subcuenta
    browser.ir_a_pag(
        reverse('cuenta', args=[ssc1.slug])
    )

    # Vemos el nombre de la cuenta encabezando la página
    browser.comparar_cuenta(ssc1)

    # Y vemos que al lado del nombre aparece el saldo de la cuenta
    browser.comparar_saldo_de(ssc1)

    # Y vemos que antes del nombre y saldo de la cuenta aparece en tipografía
    # menos destacada el nombre y saldo de sus cuentas ancestro
    saldos_ancestro = [
        x.text for x in browser.esperar_elementos("class_div_saldo_ancestro")
    ]
    assert \
        saldos_ancestro == [
            f"Saldo de cuenta madre {cuenta_de_dos_titulares.nombre}: "
            f"{float_format(cuenta_de_dos_titulares.saldo)}",
            f"Saldo de cuenta madre {scot_acumulativa.nombre}: "
            f"{float_format(scot_acumulativa.saldo)}",
        ]

    # Y vemos que luego del nombre y saldo de la cuenta aparece en la misma
    # tipografía menos destacada el nombre y saldo de sus cuentas hermanas
    saldos_hermana = [
        x.text for x in browser.esperar_elementos("class_div_saldo_hermana")
    ]
    assert \
        saldos_hermana == [
            f"Saldo de cuenta hermana subsubcuenta 2: {float_format(ssc2.saldo)}",
            f"Saldo de cuenta hermana subsubcuenta 3: {float_format(ssc3.saldo)}",
        ]

    # Cliqueamos en un movimiento
    links_movimiento = browser.esperar_elementos("class_link_movimiento")
    links_movimiento[2].click()

    # Vemos que en la sección de movimientos aparecen los movimientos de la
    # cuenta o sus subcuentas, con el movimiento cliqueado resaltado
    browser.comparar_movimientos_de(ssc1)
    movimientos = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movimientos[2].get_attribute("class")

    # Y vemos que en el saldo general de la página aparece el saldo histórico
    # de la cuenta acumulativa al momento del movimiento
    movimiento = ssc1.movs().order_by('-fecha', '-orden_dia')[2]
    assert movimiento.concepto == movimientos[2].find_element_by_class_name(
        "class_td_concepto").text
    assert \
        ssc1.saldo != ssc1.saldo_en_mov(movimiento)
    assert \
        browser.esperar_elemento("id_importe_saldo_gral").text == \
        float_format(ssc1.saldo_en_mov(movimiento))

    # Y vemos que al lado de cada una de las cuentas ancestro aparece el
    # saldo histórico de la cuenta al momento del movimiento
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_div_saldo_ancestro")]
    for index, cta in enumerate(reversed(ssc1.ancestros())):
        assert saldos_historicos[index].replace(
            f'Saldo de cuenta madre {cta.nombre}: ', ''
        ) == float_format(cta.saldo_en_mov(movimiento))

    # Y vemos que al lado de cada una de las subcuentas hermanas aparece el
    # saldo histórico de la subcuenta al momento del movimiento
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_div_saldo_hermana")]
    for index, cta in enumerate(ssc1.hermanas()):
        assert saldos_historicos[index].replace(
            f'Saldo de cuenta hermana {cta.nombre}: ', ''
        ) == float_format(cta.saldo_en_mov(movimiento))
