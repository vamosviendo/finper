from django.urls import reverse
from selenium.webdriver.common.by import By

from diario.models import Movimiento


def test_permite_activar_cuentas_inactivas(browser, cuenta_inactiva, cuenta):
    # En la página de cuentas inactivas, al lado de cada cuenta hay una opción "A"
    # Si cliqueamos en esa opción y pulsamos el botón de confirmación, la cuenta se activa.
    browser.ir_a_pag(reverse("ctas_inactivas"))
    browser.encontrar_elemento("A", By.LINK_TEXT).click()
    browser.pulsar("id_btn_confirm")
    browser.assert_url(reverse("ctas_inactivas"))

    # La cuenta desaparece de la página de cuentas inactivas
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta', fail=False)]
    assert cuenta_inactiva.nombre not in nombres_cuenta

    # y aparece entre las cuentas de la página principal
    browser.ir_a_pag()
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta', fail=False)]
    assert cuenta_inactiva.nombre in nombres_cuenta


def test_muestra_cuenta_madre_antes_de_subcuenta_inactiva(browser, cuenta_acumulativa_saldo_0):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    sc3 = cuenta_acumulativa_saldo_0.agregar_subcuenta("subcuenta 3", "sc3", sc1.titular)
    sc1.activa = False
    sc1.clean_save()
    sc3.activa = False
    sc3.clean_save()

    # Si una o más subcuentas de una cuenta acumulativa están en la página
    # de cuentas inactivas, se muestra encima de ella su cuenta madre.
    browser.ir_a_pag(reverse("ctas_inactivas"))
    cuentas = browser.encontrar_elementos("class_link_cuenta")
    nombres_cuenta = [x.text for x in cuentas]
    assert nombres_cuenta == [cuenta_acumulativa_saldo_0.nombre, sc1.nombre, sc3.nombre]


def test_no_muestra_dias_ni_movimientos_excepto_en_detalle_de_cuenta_inactiva(browser, cuenta, entrada, salida):
    # En la página de cuentas inactivas, por razones de rendimiento, no se muestran los movimientos
    Movimiento.crear("puesta en cero", cuenta.saldo(), cta_salida=cuenta)
    cuenta.refresh_from_db()
    cuenta.activa = False
    cuenta.clean_save()

    browser.ir_a_pag(reverse("ctas_inactivas"))
    browser.no_encontrar_elemento("id_section_movimientos")

    # Sí se muestran los movimientos si vamos al detalle de cualquier cuenta inactiva
    browser.ir_a_pag(cuenta.get_absolute_url())
    browser.encontrar_elemento("id_section_movimientos")
