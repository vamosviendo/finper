from typing import List

import pytest
from django.urls import reverse
from django.utils.formats import number_format
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from utils.numeros import float_format, format_float
from utils.tiempo import hoy
from vvsteps.driver import MiWebElement


def textos_hijos(elemento: MiWebElement, tag_subelem: str) -> List[str]:
    return [x.text for x in elemento.find_elements_by_tag_name(tag_subelem)]


def test_crear_movimiento(browser, cuenta):
    """ Cuando vamos a la página de cuenta nueva y completamos el formulario,
        aparece un movimiento nuevo al tope de la lista de movimientos. """
    valores = {
        "fecha": "2010-12-05",
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
    lista_movs = browser.esperar_elemento("id_section_movimientos")
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
    cuenta_mov = mov.find_element_by_class_name("class_td_cta_entrada").text
    assert cuenta_mov == cuenta.nombre

    # El saldo de la cuenta sobre la que se realizó el movimiento y el saldo
    # general de la página reflejan el cambio provocado por el nuevo movimiento
    assert browser.esperar_saldo_en_moneda_de_cuenta(cuenta.slug).text == importe_localizado
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
        browser, cuenta, cuenta_ajena, cuenta_2, cuenta_ajena_2):
    # Si generamos un movimiento entre cuentas de distintos titulares, se
    # genera un contramovimiento por el mismo importes entre cuentas
    # generadas automáticamente con los titulares invertidos

    # Completamos el form de movimiento nuevo, seleccionando cuentas de
    # titulares distintos en los campos de cuentas
    browser.crear_movimiento(
        concepto="Préstamo",
        importe="30",
        cta_entrada=cuenta.nombre,
        cta_salida=cuenta_ajena.nombre
    )
    emisor = cuenta_ajena.titular
    receptor = cuenta.titular

    # Vemos que además del movimiento creado se generó un movimiento automático
    # con las siguientes características:
    # - concepto "{concepto}"
    mov = browser.esperar_movimiento("concepto", "Préstamo")
    contramov = browser.esperar_movimiento("concepto", "Constitución de crédito")
    celdas_mov = textos_hijos(mov, "td")
    celdas_contramov = textos_hijos(contramov, "td")

    # - los nombres de los titulares en el detalle
    assert celdas_contramov[2] == f"de {emisor.nombre} a {receptor.nombre}"

    # - el mismo importe que el movimiento creado
    assert celdas_mov[3] == celdas_contramov[3] == float_format(30)

    # - dos cuentas generadas automáticamente a partir de los titulares,
    #   con la cuenta del titular de la cuenta de entrada del movimiento
    #   creado como cuenta de salida, y viceversa
    assert celdas_mov[4] == cuenta.nombre
    assert celdas_mov[5] == cuenta_ajena.nombre
    assert celdas_contramov[4] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    assert celdas_contramov[5] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()

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
    link_cuenta = browser.esperar_elemento(f"id_link_cta__{emisor.titname}-{receptor.titname}")
    saldo_cuenta = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.titname}-{receptor.titname}")
    assert \
        link_cuenta.text == \
        f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    assert saldo_cuenta.text == float_format(30)

    # Si generamos otro movimiento entre las mismas cuentas, el
    # contramovimiento se genera con concepto "Aumento de crédito" y el
    # saldo de las cuentas automáticas suma el importe del movimiento
    browser.crear_movimiento(
        concepto="Otro préstamo",
        importe="10",
        cta_entrada=cuenta.nombre,
        cta_salida=cuenta_ajena.nombre
    )
    contramov = browser.esperar_movimiento("concepto", "Aumento de crédito")
    celdas_contramov = textos_hijos(contramov, "td")
    assert celdas_contramov[3] == float_format(10)
    assert celdas_contramov[4] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    assert celdas_contramov[5] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.titname}-{receptor.titname}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.titname}-{emisor.titname}")
    assert saldo_cuenta_acreedora.text == float_format(30+10)
    assert saldo_cuenta_deudora.text == float_format(-30-10)

    # Si generamos un movimiento entre las mismas cuentas pero invertidas,
    # el contramovimiento se genera con concepto "Pago a cuenta de crédito" y
    # el importe se resta del saldo de las cuentas automáticas
    browser.crear_movimiento(
        concepto="Devolución parcial",
        importe="15",
        cta_entrada=cuenta_ajena.nombre,
        cta_salida=cuenta.nombre
    )
    contramov = browser.esperar_movimiento("concepto", "Pago a cuenta de crédito")
    celdas_contramov = textos_hijos(contramov, "td")
    assert celdas_contramov[3] == float_format(15)
    assert celdas_contramov[4] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()
    assert celdas_contramov[5] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.titname}-{receptor.titname}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.titname}-{emisor.titname}")
    assert saldo_cuenta_acreedora.text == float_format(30+10-15)
    assert saldo_cuenta_deudora.text == float_format(-30-10+15)

    # Si generamos un movimiento entre otras cuentas de los mismos titulares,
    # sucede lo mismo que si usáramos las cuentas originales
    browser.crear_movimiento(
        concepto="Devolución parcial con otras cuentas",
        importe="7",
        cta_entrada=cuenta_ajena_2.nombre,
        cta_salida=cuenta_2.nombre
    )
    contramov = browser.esperar_movimiento("concepto", "Pago a cuenta de crédito")
    celdas_contramov = textos_hijos(contramov, "td")
    assert celdas_contramov[3] == float_format(7)
    assert celdas_contramov[4] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()
    assert celdas_contramov[5] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.titname}-{receptor.titname}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.titname}-{emisor.titname}")
    assert saldo_cuenta_acreedora.text == float_format(30+10-15-7)
    assert saldo_cuenta_deudora.text == float_format(-30-10+15+7)

    # Si generamos un movimiento entre ambos titulares con importe mayor al
    # total de la deuda:
    # - el contramovimiento se genera con concepto ""
    # - las cuentas crédito cambian de nombre y de slug (deuda de receptor con emisor se convierte en
    #   préstamo de receptor a emisor y viceversa)
    browser.crear_movimiento(
        concepto="Devolución con exceso",
        importe="20",
        cta_entrada=cuenta_ajena.nombre,
        cta_salida=cuenta.nombre
    )
    contramov = browser.esperar_movimiento("concepto", "Pago en exceso de crédito")
    celdas_contramov = textos_hijos(contramov, "td")
    assert celdas_contramov[3] == float_format(20)
    assert celdas_contramov[4] == f"préstamo de {receptor.nombre} a {emisor.nombre}".lower()
    assert celdas_contramov[5] == f"deuda de {emisor.nombre} con {receptor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.titname}-{emisor.titname}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.titname}-{receptor.titname}")
    assert saldo_cuenta_acreedora.text == float_format(-30-10+15+7+20)
    assert saldo_cuenta_deudora.text == float_format(30+10-15-7-20)

    # Si generamos un movimiento entre ambos titulares con importe igual al
    # total de la deuda, el contramovimiento se genera con concepto
    # "Cancelación de crédito"...
    browser.crear_movimiento(
        concepto="Devolución total",
        importe="2",
        cta_entrada=cuenta.nombre,
        cta_salida=cuenta_ajena.nombre
    )
    contramov = browser.esperar_movimiento("concepto", "Cancelación de crédito")
    celdas_contramov = textos_hijos(contramov, "td")
    assert celdas_contramov[3] == float_format(2)
    assert celdas_contramov[4] == f"deuda de {emisor.nombre} con {receptor.nombre}".lower()
    assert celdas_contramov[5] == f"préstamo de {receptor.nombre} a {emisor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.titname}-{receptor.titname}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.titname}-{emisor.titname}")
    assert saldo_cuenta_acreedora.text == float_format(30+10-15-7-18)
    assert saldo_cuenta_deudora.text == float_format(-30-10+15+7+18)


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


def test_crear_movimiento_con_cuenta_en_moneda_no_base(browser, cuenta_en_dolares, euro, fecha, importe):
    browser.ir_a_pag()
    # Dada una cuenta en dolares
    saldo_base_original = format_float(browser.esperar_saldo_en_moneda_de_cuenta(cuenta_en_dolares.slug).text)

    # Cuando generamos un movimiento de entrada sobre dicha cuenta
    browser.crear_movimiento(
        concepto='Movimiento en dólares',
        importe=str(importe),
        fecha=fecha,
        cta_entrada=cuenta_en_dolares.nombre,
        moneda=euro.nombre,
    )
    # Si seleccionamos para el importe una moneda distinta de la moneda de
    # la cuenta, recibimos un mensaje de error
    lista_errores = browser.esperar_elemento("ul.errorlist", By.CSS_SELECTOR)
    assert "El movimiento debe ser expresado en dólares" in lista_errores.text

    # Si seleccionamos para el importe la moneda de la cuenta, se nos permite
    # completar el movimiento
    browser.completar("id_moneda", cuenta_en_dolares.moneda.nombre)
    browser.pulsar()

    # Somos dirigidos a la página principal donde podemos ver que el saldo
    # principal de la cuenta cambió en el importe registrado en el movimiento,
    browser.assert_url(reverse('home'))
    saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cuenta_en_dolares.slug)
    assert saldo_base.text == float_format(saldo_base_original + importe)


def test_crear_traspaso_entre_cuentas_en_distinta_moneda(browser, cuenta_con_saldo, cuenta_con_saldo_en_dolares, fecha):
    # Dadas una cuenta en pesos y una cuenta en dólares

    # Si vamos a generar un movimiento de traspaso de una a otra

    # Vemos que junto al campo "importe" aparece un campo "moneda"

    # Este campo nos permite seleccionar la moneda en la que estará expresado
    # el movimiento, siendo las opciones las monedas de las dos cuentas
    # intervinientes.
    browser.crear_movimiento(

    )
    ...


def test_modificar_movimiento(browser, entrada, cuenta_2):
    # Las modificaciones hechas mediante el formulario de movimiento se ven
    # reflejadas en el movimiento que se muestra en la página principal
    browser.ir_a_pag(reverse('mov_mod', args=[entrada.pk]))
    browser.completar_form(
        concepto='Movimiento con concepto modificado',
        cta_entrada='cuenta 2',
        importe='124',
    )
    browser.assert_url(reverse('home'))
    concepto_movimiento = browser.esperar_elemento(f"id_link_mov_{entrada.identidad}").text.strip()
    assert concepto_movimiento == "Movimiento con concepto modificado"
    fila_movimiento = browser.esperar_elemento(f"id_row_mov_{entrada.identidad}")
    cuenta_movimiento = fila_movimiento.esperar_elemento('class_td_cta_entrada', By.CLASS_NAME).text.strip()
    assert cuenta_movimiento == cuenta_2.nombre
    importe_movimiento = fila_movimiento.esperar_elemento('class_td_importe', By.CLASS_NAME).text.strip()
    assert importe_movimiento == "124,00"


def test_convertir_entrada_en_traspaso_entre_titulares(browser, entrada, cuenta_ajena):
    # Cuando se agrega a un movimiento de entrada una cuenta ajena como cuenta
    # de salida, se genera un contramovimiento con la misma fecha del movimiento
    browser.ir_a_pag()
    cantidad_movimientos = len(browser.esperar_elementos('class_row_mov'))
    browser.ir_a_pag(reverse('mov_mod', args=[entrada.pk]))
    browser.completar_form(cta_salida=cuenta_ajena.nombre, esgratis='False')
    assert len(browser.esperar_elementos('class_row_mov')) == cantidad_movimientos + 1
    mov_nuevo = browser.esperar_elemento('class_row_mov', By.CLASS_NAME)
    assert mov_nuevo.esperar_elemento('class_td_concepto', By.CLASS_NAME).text == 'Constitución de crédito'
    assert mov_nuevo.esperar_elemento('class_td_fecha', By.CLASS_NAME).text == entrada.fecha.strftime("%Y-%m-%d")


def test_eliminar_movimiento(browser, entrada, salida):
    # Cuando se elimina un movimiento desaparece de la página principal
    concepto = entrada.concepto
    browser.ir_a_pag(reverse('mov_elim', args=[entrada.pk]))
    browser.pulsar('id_btn_confirm')
    browser.assert_url(reverse('home'))
    conceptos = [x.text.strip() for x in browser.esperar_elementos('class_link_movimiento')]
    assert concepto not in conceptos
