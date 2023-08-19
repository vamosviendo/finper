from typing import List

import pytest
from django.urls import reverse
from django.utils.formats import number_format
from selenium.common.exceptions import NoSuchElementException

from diario.models import Cuenta
from utils.numeros import float_format
from utils.tiempo import hoy
from vvsteps.driver import MiWebElement


def textos_hijos(elemento: MiWebElement, tag_subelem: str) -> List[str]:
    return [x.text for x in elemento.find_elements_by_tag_name(tag_subelem)]


def test_ir_a_crear_movimiento(browser, cuenta):
    """ Cuando cliqueamos en el botón "Movimiento nuevo" de la página principal,
        somos dirigidos a la página correspondiente"""
    browser.ir_a_pag()
    browser.esperar_elemento("id_link_mov_nuevo").click()
    browser.assert_url(reverse("mov_nuevo"))


def test_crear_movimiento(browser, cuenta):
    """ Cuando vamos a la página de cuenta nueva y completamos el formulario,
        aparece un movimiento nuevo al tope de la lista de movimientos. """
    valores = {
        "fecha": "2008-08-05",
        "concepto": "Entrada",
        "cta_entrada": "cuenta",
        "importe": "50.00"
    }

    browser.ir_a_pag(reverse("mov_nuevo"))

    # Al entrar a la página veo un formulario de movimiento
    form_mov = browser.esperar_elemento("id_form_movimiento")

    # El campo "fecha" del formulario tiene la fecha de hoy como valor por
    # defecto
    assert \
        form_mov.find_element_by_id("id_fecha").get_attribute("value") == \
        hoy()

    # Cargamos los valores necesarios para generar un movimiento nuevo
    browser.completar_form(**valores)

    # En la lista de movimientos, aparece un movimiento nuevo
    lista_movs = browser.esperar_elemento("id_lista_ult_movs")
    movs = lista_movs.find_elements_by_tag_name("tr")[1:]   # se descarta el encabezado
    assert len(movs) == 1

    # Los valores del movimiento aparecido coinciden con los que ingresamos en
    # el formulario de carga
    mov = movs[0]

    for campo in ["fecha", "concepto"]:
        assert \
            mov.find_element_by_class_name(f"class_td_{campo}").text == \
            valores[campo]
    importe_localizado = number_format(float(valores["importe"]), 2)
    assert mov.find_element_by_class_name(f"class_td_importe").text == \
        importe_localizado
    cuentas = mov.find_element_by_class_name("class_td_cuentas").text
    assert cuentas == f'+{cuenta.slug}'

    # El saldo de la cuenta sobre la que se realizó el movimiento y el saldo
    # general de la página reflejan el cambio provocado por el nuevo movimiento
    assert \
        browser.esperar_elemento(f'id_saldo_cta_{cuenta.slug}').text == \
        importe_localizado
    assert \
        browser.esperar_elemento('id_importe_saldo_gral').text == \
        importe_localizado


def test_cuentas_acumulativas_no_aparecen_entre_las_opciones_de_cuenta(
        browser, cuenta, cuenta_acumulativa):
    browser.ir_a_pag(reverse('mov_nuevo'))
    opciones_ce = browser.esperar_opciones_de_campo("cta_entrada")
    opciones_cs = browser.esperar_opciones_de_campo("cta_salida")
    assert cuenta.nombre.lower() in opciones_ce
    assert cuenta.nombre.lower() in opciones_cs
    assert \
        cuenta_acumulativa.nombre.lower() not in \
        [x.lower() for x in opciones_ce]
    assert \
        cuenta_acumulativa.nombre.lower() not in \
        [x.lower() for x in opciones_cs]


def test_crear_creditos_o_devoluciones(
        browser,
        titular, otro_titular,
        cuenta, cuenta_ajena,
        cuenta_2, cuenta_ajena_2):

    def chequear_mov_y_contramov(
            concepto: str, importe: float,
            cta_entrada: Cuenta, cta_salida: Cuenta,
            concepto_contramov: str, saldo: float):
        receptor = cta_entrada.titular
        emisor = cta_salida.titular
        slug_cta_acreedora = f'_{emisor.titname}-{receptor.titname}'
        slug_cta_deudora = f'_{receptor.titname}-{emisor.titname}'

        # Completamos el form de movimiento nuevo, seleccionando cuentas de
        # titulares distintos en los campos de cuentas
        browser.crear_movimiento(
            concepto=concepto,
            importe=str(importe),
            cta_entrada=cta_entrada.nombre,
            cta_salida=cta_salida.nombre
        )

        # Vemos que además del movimiento creado se generó un movimiento automático
        # con las siguientes características:
        # - concepto "{concepto}"
        mov = browser.esperar_movimiento("concepto", concepto)
        contramov = browser.esperar_movimiento("concepto", concepto_contramov)
        celdas_mov = textos_hijos(mov, "td")
        celdas_contramov = textos_hijos(contramov, "td")

        # - los nombres de los titulares en el detalle
        assert celdas_contramov[2] == f"de {emisor.nombre} a {receptor.nombre}"

        # - el mismo importe que el movimiento creado
        assert celdas_mov[3] == celdas_contramov[3] == float_format(importe)

        # - dos cuentas generadas automáticamente a partir de los titulares,
        #   con la cuenta del titular de la cuenta de entrada del movimiento
        #   creado como cuenta de salida, y viceversa
        assert celdas_mov[4] == f"+{cta_entrada.slug} -{cta_salida.slug}"
        assert \
            celdas_contramov[4] == \
            f"+{slug_cta_acreedora} -{slug_cta_deudora}"

        # - a diferencia del movimiento creado manualmente, no muestra botones
        #   de editar o borrar.
        assert mov.find_element_by_class_name("class_link_elim_mov").text == "B"
        assert mov.find_element_by_class_name("class_link_mod_mov").text == "E"
        with pytest.raises(NoSuchElementException):
            contramov.find_element_by_class_name("class_link_elim_mov")
        with pytest.raises(NoSuchElementException):
            contramov.find_element_by_class_name("class_link_mod_mov")

        # Si vamos a la página de detalles del titular de la cuenta de salida,
        # vemos entre sus cuentas la cuenta generada automáticamente que lo
        # muestra como acreedor, con saldo igual a {saldo}
        browser.ir_a_pag(reverse('titular', args=[emisor.titname]))
        link_cuenta = browser.esperar_elemento(f"id_link_cta_{slug_cta_acreedora}")
        saldo_cuenta = browser.esperar_elemento(f"id_saldo_cta_{slug_cta_acreedora}")
        assert \
            link_cuenta.text == \
            f"préstamo entre {emisor.titname} y {receptor.titname}"
        assert saldo_cuenta.text == float_format(saldo)

        # Si vamos a la página de detalles del titular de la cuenta de entrada,
        # vemos entre sus cuentas la cuenta generada automáticamente que lo
        # muestra como deudor, con saldo igual al negativo de {saldo}
        if saldo != 0:
            browser.ir_a_pag(reverse('titular', args=[receptor.titname]))
            link_cuenta = browser.esperar_elemento(f"id_link_cta_{slug_cta_deudora}")
            saldo_cuenta = browser.esperar_elemento(f"id_saldo_cta_{slug_cta_deudora}")
            assert \
                link_cuenta.text == \
                f"préstamo entre {receptor.titname} y {emisor.titname}"
            assert saldo_cuenta.text == float_format(-saldo)
        else:
            with pytest.raises(NoSuchElementException):
                browser.esperar_elemento(f"id_link_cta_{slug_cta_deudora}")

    # Si generamos un movimiento entre cuentas de distintos titulares, se
    # genera un contramovimiento por el mismo importes entre cuentas
    # generadas automáticamente con los titulares invertidos
    chequear_mov_y_contramov(
        "Préstamo", 30, cuenta, cuenta_ajena, "Constitución de crédito", 30
    )

    # Si generamos otro movimiento entre las mismas cuentas, el
    # contramovimiento se genera con concepto "Aumento de crédito" y el
    # saldo de las cuentas automáticas suma el importe del movimiento
    chequear_mov_y_contramov(
        "Otro préstamo", 10, cuenta, cuenta_ajena, "Aumento de crédito", 40
    )

    # Si generamos un movimiento entre las mismas cuentas pero invertidas,
    # el contramovimiento se genera con concepto "Pago a cuenta de crédito" y
    # el importe se resta del saldo de las cuentas automáticas
    chequear_mov_y_contramov(
        "Devolución parcial", 15, cuenta_ajena, cuenta,
        "Pago a cuenta de crédito", -25
    )

    # Si generamos un movimiento entre otras cuentas de los mismos titulares,
    # sucede lo mismo que si usáramos las cuentas originales
    chequear_mov_y_contramov(
        "Devolución parcial con otras cuentas", 7, cuenta_ajena_2, cuenta_2,
        "Pago a cuenta de crédito", -18
    )

    # Si generamos un movimiento entre ambos titulares con importe igual al
    # total de la deuda, el contramovimiento se genera con concepto
    # "Cancelación de crédito"...
    chequear_mov_y_contramov(
        "Devolución total", 18, cuenta_ajena, cuenta,
        "Cancelación de crédito", 0
    )


def test_crear_traspaso_entre_titulares_sin_deuda(browser, cuenta, cuenta_ajena):
    # Antes de empezar, tomamos los valores de los capitales mostrados en las
    # páginas de detalle de los titulares cuyas cuentas usaremos
    browser.ir_a_pag(
        reverse("titular", args=[cuenta_ajena.titular.titname]))
    capital_emisor = browser.esperar_elemento(
        f"id_capital_{cuenta_ajena.titular.titname}").text
    browser.ir_a_pag(
        reverse("titular", args=[cuenta.titular.titname]))
    capital_receptor = browser.esperar_elemento(
        f"id_capital_{cuenta.titular.titname}").text


    # Completamos el form de movimiento nuevo, seleccionando cuentas de
    # titulares distintos en los campos de cuentas. Cliqueamos en la casilla
    # "esgratis"
    browser.crear_movimiento(
        concepto="Donación",
        importe="30",
        cta_entrada=cuenta.nombre,
        cta_salida=cuenta_ajena.nombre,
        esgratis=True
    )

    # Vemos que sólo se genera el movimiento creado, sin que se genere ningún
    # movimiento automático de deuda.
    mov = browser.esperar_movimiento("concepto", "Donación")
    with pytest.raises(NoSuchElementException):
        browser.esperar_movimiento("concepto", "Constitución de crédito")

    # Si vamos a la página de detalles del titular de la cuenta de salida
    # (emisor), vemos que entre sus cuentas no hay ninguna generada automáticamente, sólo
    # las cuentas regulares-
    browser.ir_a_pag(reverse("titular", args=[cuenta_ajena.titular.titname]))
    cuentas_pag = [
        x.text for x in browser.esperar_elementos("class_link_cuenta")
    ]
    cuenta_credito = \
        f"_{cuenta_ajena.titular.titname}-{cuenta.titular.titname}".upper()
    assert \
        cuenta_credito not in cuentas_pag, \
        f"Cuenta {cuenta_credito}, que no debería existir, existe"

    # Y vemos que el capital del emisor disminuyó en un importe igual al del
    # movimiento que creamos
    assert capital_emisor == float_format(cuenta_ajena.titular.capital + 30)

    # Lo mismo con el titular de la cuenta de entrada.
    browser.ir_a_pag(reverse("titular", args=[cuenta.titular.titname]))
    cuentas_pag = [
        x.text for x in browser.esperar_elementos("class_link_cuenta")
    ]
    cuenta_credito = \
        f"_{cuenta.titular.titname}-{cuenta_ajena.titular.titname}".upper()
    assert \
        cuenta_credito not in cuentas_pag, \
        f"Cuenta {cuenta_credito}, que no debería existir, existe"
    assert capital_receptor == float_format(cuenta.titular.capital - 30)
