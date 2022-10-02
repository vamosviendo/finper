import pytest
from django.urls import reverse

from diario.models import CuentaAcumulativa, CuentaInteractiva, Titular, Movimiento


@pytest.fixture
def cuenta_de_dos_titulares(
        titular_gordo: Titular,
        cuenta_ajena: CuentaInteractiva,
) -> CuentaAcumulativa:
    return cuenta_ajena.dividir_y_actualizar(
        {
            'nombre': 'Subcuenta otro titular',
            'slug': 'scot',
            'saldo': cuenta_ajena.saldo - 10
        },
        {
            'nombre': 'Subcuenta titular gordo',
            'slug': 'sctg',
            'saldo': 10,
            'titular': titular_gordo
        }
    )


@pytest.fixture
def credito_entre_subcuentas(cuenta_de_dos_titulares: CuentaAcumulativa) -> Movimiento:
    scot, sctg = cuenta_de_dos_titulares.subcuentas.all()
    return Movimiento.crear('Crédito entre subcuentas', 50, scot, sctg)


def test_detalle_de_cuentas(
        browser,
        titular, otro_titular, titular_gordo,
        cuenta_con_saldo, cuenta_de_dos_titulares,
        credito_entre_subcuentas):
    # Vamos a la página de inicio
    browser.ir_a_pag()

    # Cliqueamos en el nombre de una cuenta
    browser.cliquear_en_cuenta(cuenta_con_saldo)

    # Vemos el titular de la cuenta y los movimientos en los que interviene
    browser.comparar_titular_de(cuenta_con_saldo)
    browser.comparar_movimientos_de(cuenta_con_saldo)

    # Volvemos a la página principal y cliqueamos en el nombre de una cuenta
    # acumulativa
    browser.ir_a_pag()
    browser.cliquear_en_cuenta(cuenta_de_dos_titulares)

    # Vemos las subcuentas de la cuenta acumulativa, los titulares de las
    # subcuentas y los movimientos relacionados con ella o sus subcuentas
    nombres_subcuenta = [x.text for x in browser.esperar_elementos(
        'class_link_cuenta'
    )]
    assert nombres_subcuenta == [
        x.slug.upper() for x in cuenta_de_dos_titulares.subcuentas.all()
    ]

    nombres_titular = [
        x.text.strip() for x in browser.esperar_elementos(
            'class_div_nombre_titular'
    )]
    assert nombres_titular == [
        x.nombre for x in cuenta_de_dos_titulares.titulares
    ]
    browser.comparar_movimientos_de(cuenta_de_dos_titulares)

    # Cliqueamos en el nombre de la primera subcuenta
    primera_subcuenta = cuenta_de_dos_titulares.subcuentas.first()
    browser.cliquear_en_cuenta(primera_subcuenta)

    # Vemos el titular de la primera subcuenta y los movimientos en los que
    # interviene
    browser.comparar_titular_de(primera_subcuenta)
    browser.comparar_movimientos_de(primera_subcuenta)

    # Volvemos a la página de la cuenta acumulativa y cliqueamos en el nombre
    # de la segunda subcuenta
    browser.ir_a_pag(
        reverse('cta_detalle', args=[cuenta_de_dos_titulares.slug])
    )
    segunda_subcuenta = cuenta_de_dos_titulares.subcuentas.last()
    browser.cliquear_en_cuenta(segunda_subcuenta)

    # Vemos el titular de la segunda subcuenta y los movimientos en los que
    # interviene
    browser.comparar_titular_de(segunda_subcuenta)
    browser.comparar_movimientos_de(segunda_subcuenta)
