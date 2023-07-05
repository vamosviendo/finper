import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By

from diario.models import CuentaAcumulativa, Movimiento
from pytests.functional.helpers import texto_en_hijos_respectivos
from utils.numeros import float_format


@pytest.fixture
def credito_entre_subcuentas(cuenta_de_dos_titulares: CuentaAcumulativa) -> Movimiento:
    scot, sctg = cuenta_de_dos_titulares.subcuentas.all()
    return Movimiento.crear('Crédito entre subcuentas', 50, scot, sctg)


def test_detalle_de_cuenta_interactiva(
        browser,
        titular, otro_titular, titular_gordo,
        cuenta_con_saldo, entrada_otra_cuenta):
    # Vamos a la página de inicio
    browser.ir_a_pag()

    # Cliqueamos en el nombre de una cuenta interactiva
    browser.cliquear_en_cuenta(cuenta_con_saldo)

    # Vemos el nombre de la cuenta encabezando la página
    browser.comparar_cuenta(cuenta_con_saldo)

    # Y vemos que al lado del nombre aparece el saldo de la cuenta
    browser.comparar_saldo_de(cuenta_con_saldo)

    # Y vemos que en la sección de titulares aparece el titular de la cuenta
    divs_titular = browser.esperar_elementos("class_div_titular")
    assert len(divs_titular) == 1
    nombres = texto_en_hijos_respectivos("class_div_nombre_titular", divs_titular)
    assert nombres[0] == cuenta_con_saldo.titular.nombre

    # Y vemos que no aparecen cuentas en la sección de cuentas
    assert browser.esperar_elementos('class_link_cuenta', fail=False) == []

    # Y vemos que solo los movimientos en los que interviene la cuenta aparecen
    # en la sección de movimientos
    browser.comparar_movimientos_de(cuenta_con_saldo)
    assert not set(cuenta_con_saldo.movs()) == set(Movimiento.todes())

    # Cuando cliqueamos en el ícono de agregar cuenta, accedemos a la página
    # de dividir cuenta en subcuentas
    browser.esperar_elemento("id_link_cuenta_nueva").click()
    browser.assert_url(reverse('cta_div', args=[cuenta_con_saldo.slug]))


def test_detalle_de_cuenta_acumulativa(
        browser, entrada_otra_cuenta, cuenta_de_dos_titulares, credito_entre_subcuentas):

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

    # Cliqueamos en el nombre de la primera subcuenta
    primera_subcuenta = cuenta_de_dos_titulares.subcuentas.first()
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

    # Y vemos el titular de la primera subcuenta y los movimientos en los que
    # interviene

    browser.comparar_titulares_de(primera_subcuenta)
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
    browser.comparar_titulares_de(segunda_subcuenta)
    browser.comparar_movimientos_de(segunda_subcuenta)


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
    scot = CuentaAcumulativa.tomar(pk=scot_pk)

    # Cuando vamos a la página de la primer sub-subcuenta
    browser.ir_a_pag(
        reverse('cta_detalle', args=[ssc1.slug])
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
            f"Saldo de cuenta madre {scot.nombre}: "
            f"{float_format(scot.saldo)}",
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
