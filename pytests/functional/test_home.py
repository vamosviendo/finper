from __future__ import annotations

from typing import List

from selenium.webdriver.remote.webelement import WebElement

from diario.utils import saldo_general_historico
from utils.numeros import float_format
from vvsteps.driver import MiWebElement


def hijos(classname: str, lista_elementos: List[MiWebElement | WebElement]) -> List[str]:
    return [
        x.find_element_by_class_name(classname).text
        for x in lista_elementos
    ]


def test_home(
        browser, titular, otro_titular,
        cuenta, cuenta_2, cuenta_3,
        entrada, traspaso, entrada_posterior_otra_cuenta):
    # vamos a la página principal
    browser.ir_a_pag()

    # Vemos dos titulares en la sección de titulares: el titular por defecto
    # y el cargado por nosotros.
    titulares = browser.esperar_elementos("class_div_titular")
    assert len(titulares) == 2
    nombres = hijos("class_div_nombre_titular", titulares)
    assert nombres[0] == titular.nombre
    assert nombres[1] == otro_titular.nombre

    # Vemos que cada titular de la sección de titulares muestra el capital del
    # titular
    capitales = hijos("class_capital_titular", titulares)
    assert capitales[0] == float_format(
        cuenta.saldo + cuenta_2.saldo + cuenta_3.saldo
    )
    assert capitales[1] == '0,00'

    # Vemos tres cuentas en la sección de cuentas, con nombres correspondientes
    # al slug de cada una de las cuentas existentes en mayúsculas.
    cuentas = browser.find_elements_by_class_name("class_div_cuenta")
    assert len(cuentas) == 3
    nombres_cuenta = hijos("class_nombre_cuenta", cuentas)
    assert nombres_cuenta[0] == cuenta.slug.upper()
    assert nombres_cuenta[1] == cuenta_2.slug.upper()
    assert nombres_cuenta[2] == cuenta_3.slug.upper()

    # El saldo de cada una de las cuentas corresponde a los movimientos en los
    # que participó
    saldos = hijos("class_saldo_cuenta", cuentas)
    assert saldos[0] == float_format(entrada.importe + traspaso.importe)
    assert saldos[1] == float_format(
        entrada_posterior_otra_cuenta.importe - traspaso.importe)
    assert saldos[2] == '0,00'

    # Vemos tres movimientos en la sección de movimientos, con conceptos
    # correspondientes al concepto de cada uno de los movimientos existentes.
    movimientos = browser.find_elements_by_class_name("class_row_mov")
    objs_mov = [entrada_posterior_otra_cuenta, traspaso, entrada]
    assert len(movimientos) == 3
    fechas = hijos("class_td_fecha", movimientos)
    conceptos = hijos("class_td_concepto", movimientos)
    importes = hijos("class_td_importe", movimientos)
    cuentas = hijos("class_td_cuentas", movimientos)
    generales = hijos("class_td_general", movimientos)
    for i in range(0,2):
        mov = objs_mov[i]
        assert fechas[i] == mov.fecha.strftime('%Y-%m-%d')
        assert conceptos[i] == mov.concepto
        assert importes[i] == float_format(mov.importe)
        assert cuentas[i] == mov.str_cuentas()
        assert generales[i] == float_format(saldo_general_historico(mov))
