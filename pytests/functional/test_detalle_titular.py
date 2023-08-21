import pytest
from django.urls import reverse

from utils.numeros import float_format
from .helpers import texto_en_hijos_respectivos
from diario.models import CuentaInteractiva, Movimiento, Titular


@pytest.fixture
def cuenta_titular(cuenta: CuentaInteractiva) -> CuentaInteractiva:
    Movimiento.crear('Saldo al inicio', 500, cuenta)
    return cuenta.tomar_de_bd()


@pytest.fixture
def cuenta_otro_titular(cuenta_ajena: CuentaInteractiva) -> CuentaInteractiva:
    Movimiento.crear('Saldo al inicio', 200, cuenta_ajena)
    return cuenta_ajena.tomar_de_bd()


@pytest.fixture
def cuenta_2_titular(cuenta_2: CuentaInteractiva) -> CuentaInteractiva:
    Movimiento.crear('Saldo al inicio', 150, cuenta_2)
    return cuenta_2.tomar_de_bd()


@pytest.fixture
def entrada_titular(cuenta_titular: CuentaInteractiva) -> Movimiento:
    return Movimiento.crear('Entrada en cuenta titular', 50, cuenta_titular)


@pytest.fixture
def credito_entre_titulares(
        cuenta_titular: CuentaInteractiva,
        cuenta_otro_titular: CuentaInteractiva
) -> Movimiento:
    return Movimiento.crear(
        'Credito entre titulares',
        25,
        cuenta_titular,
        cuenta_otro_titular,
    )


@pytest.fixture
def salida_otro_titular(cuenta_otro_titular: CuentaInteractiva) -> Movimiento:
    return Movimiento.crear(
        'Salida de cuenta otro titular',
        20,
        None,
        cuenta_otro_titular,
    )


def test_detalle_titular(
        browser,
        titular,
        cuenta_titular, cuenta_2_titular,
        credito_entre_titulares,
):
    # Dados dos titulares
    # Vamos a la página de inicio y cliqueamos en el primer titular
    browser.ir_a_pag()
    browser.cliquear_en_titular(titular)

    # Somos dirigidos a la página de detalle del titular cliqueado
    browser.assert_url(reverse('titular', args=[titular.titname]))

    # Vemos el nombre del titular encabezando la página
    browser.comparar_titular(titular)

    # Y vemos que al lado del nombre aparece la suma de los saldos de sus cuentas
    browser.comparar_capital_de(titular)

    # Y vemos que en la sección de titulares aparecen todos los titulares
    divs_titular = browser.esperar_elementos("class_div_titular")
    assert len(divs_titular) == Titular.cantidad()
    nombres = texto_en_hijos_respectivos("class_div_nombre_titular", divs_titular)
    assert nombres[0] == Titular.primere().nombre
    assert nombres[1] == Titular.ultime().nombre

    # Y vemos que el titular seleccionado aparece resaltado entre los demás
    # titulares
    tds_titular = browser.esperar_elementos("class_td_titular")
    tds_titular_selected = [
        x for x in tds_titular if "selected" in x.get_attribute("class")
    ]
    assert len(tds_titular_selected) == 1
    div_titular_selected = \
        tds_titular_selected[0].find_element_by_class_name(
            "class_div_nombre_titular"
        )
    assert div_titular_selected.text == titular.nombre

    # Y vemos que sólo las cuentas del titular aparecen en la sección de cuentas
    browser.comparar_cuentas_de(titular)

    # Y vemos que sólo los movimientos del titular aparecen en la sección
    # de movimientos
    browser.comparar_movimientos_de(titular)

    # Si cliqueamos en un movimiento, solo aparecen los movimientos del
    # titular en la sección de movimientos, con el movimiento cliqueado
    # resaltado
    links_movimiento = browser.esperar_elementos("class_link_movimiento")
    links_movimiento[1].click()
    browser.comparar_movimientos_de(titular)
    movs_pagina = browser.esperar_elementos("class_row_mov")
    assert "mov_selected" in movs_pagina[1].get_attribute("class")

    # Y vemos que en el saldo de la página aparece el capital histórico del
    # titular al momento del movimiento
    nombre_titular = browser.esperar_elemento(
        'id_titulo_saldo_gral'
    ).text.strip()
    movimiento = titular.movs()[2]

    assert nombre_titular == (f"Capital de {titular.nombre} histórico "
                              f"en movimiento {movimiento.orden_dia} "
                              f"del {movimiento.fecha} ({movimiento.concepto}):")
    browser.comparar_capital_historico_de(titular, movimiento)

    # Y al lado de cada cuenta del titular aparece el saldo histórico al
    # momento del movimiento seleccionado, y no aparece ninguna cuenta que no
    # pertenezca al titular
    browser.comparar_cuentas_de(titular)
    saldos_historicos = [
        x.text for x in browser.esperar_elementos("class_saldo_cuenta")]
    for index, cta in enumerate(titular.cuentas.all()):
        assert saldos_historicos[index] == float_format(cta.saldo_en_mov(movimiento))

    # Y al lado de cada titular aparece el capital histórico del titular al
    # momento del movimiento seleccionado.
    capitales_historicos = [
        x.text for x in browser.esperar_elementos("class_capital_titular")]
    for index, titular in enumerate(Titular.todes()):
        assert capitales_historicos[index] == float_format(titular.capital_historico(movimiento))

    # Y vemos una opción "Home" debajo de todos los titulares
    # Y cuando cliqueamos en la opción "Home" somos dirigidos a la página principal
    browser.esperar_elemento("id_link_home").click()
    browser.assert_url(reverse('home'))
