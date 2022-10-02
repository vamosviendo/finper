from urllib.parse import urlparse

import pytest
from django.urls import reverse

from diario.models import CuentaInteractiva, Movimiento


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
        entrada_titular, credito_entre_titulares,
):
    # Dados dos titulares
    # Vamos a la página de inicio y cliqueamos en el primer titular
    browser.ir_a_pag()
    browser.cliquear_en_titular(titular)

    # Somos dirigidos a la página de detalle del titular cliqueado
    assert \
        reverse('tit_detalle', args=[titular.titname]) == \
        urlparse(browser.current_url).path

    # Vemos el nombre del titular encabezando la página
    browser.comparar_titular(titular)

    # Y vemos que el capital del titular es igual a la suma de los saldos
    # de sus cuentas
    browser.comparar_capital_de(titular)

    # Y vemos que sólo las cuentas del titular aparecen en la sección de cuentas
    browser.comparar_cuentas_de(titular)

    # Y vemos que sólo los movimientos del titular aparecen en la sección de movimientos
    browser.comparar_movimientos_de(titular)