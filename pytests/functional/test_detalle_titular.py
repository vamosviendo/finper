import pytest
from django.urls import reverse

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
        entrada_titular, credito_entre_titulares,
):
    # Dados dos titulares
    # Vamos a la página de inicio y cliqueamos en el primer titular
    browser.ir_a_pag()
    browser.cliquear_en_titular(titular)

    # Somos dirigidos a la página de detalle del titular cliqueado
    browser.assert_url(reverse('tit_detalle', args=[titular.titname]))

    # Vemos el nombre del titular encabezando la página
    browser.comparar_titular(titular)

    # Y vemos que el capital del titular es igual a la suma de los saldos
    # de sus cuentas
    browser.comparar_capital_de(titular)

    # Y vemos que en la sección de titulares aparecen todos los titulares
    divs_titular = browser.esperar_elementos("class_div_titular")
    assert len(divs_titular) == Titular.cantidad()
    nombres = texto_en_hijos_respectivos("class_div_nombre_titular", divs_titular)
    assert nombres[0] == Titular.primere().nombre
    assert nombres[1] == Titular.ultime().nombre

    # Y vemos que el titular seleccionado aparece resaltado entre los demás
    # titulares, que aparecen atenuados
    pytest.fail("No implementado todavía")

    # Y vemos que sólo las cuentas del titular aparecen en la sección de cuentas
    browser.comparar_cuentas_de(titular)

    # Y vemos que sólo los movimientos del titular aparecen en la sección de movimientos
    browser.comparar_movimientos_de(titular)

