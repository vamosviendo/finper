from datetime import date

import pytest
from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from diario.models import Movimiento
from tests.functional.helpers import assert_exists
from utils.numeros import float_format, format_float
from utils.varios import el_que_no_es


@pytest.fixture
def valores() -> dict:
    return {
        "fecha": "2010-12-05",
        "concepto": "Entrada",
        "cta_entrada": "cuenta",
        "importe": 50.0
    }


def test_crear_movimiento(browser, cuenta, entrada, salida_posterior, dia_tardio, valores):
    """ Cuando vamos a la página de cuenta nueva y completamos el formulario,
        aparece un movimiento nuevo al tope de la lista de movimientos.
        Si después de completamos apretamos el botón "Guardar y agregar,
        se guarda el movimiento y se vuelve a abrir el formulario para cargar
        otro movimiento. """
    saldo_gral = saldo = cuenta.saldo()
    browser.ir_a_pag(reverse("mov_nuevo"))

    # Al entrar a la página veo un formulario de movimiento
    form_mov = browser.encontrar_elemento("id_form_movimiento")

    # El campo "fecha" del formulario tiene la fecha del último día con movimientos
    # como valor por defecto
    assert \
        form_mov.encontrar_elemento("id_fecha").get_attribute("value") == \
        salida_posterior.dia.fecha.strftime('%Y-%m-%d')

    # Cargamos los valores necesarios para generar un movimiento nuevo
    browser.completar_form(**valores)

    # En la lista de movimientos del día, aparece un movimiento nuevo
    dia = browser.esperar_dia(date(2010, 12, 5))
    movs_dia = dia.encontrar_elementos("class_row_mov")
    assert len(movs_dia) == 1

    # Los valores del movimiento aparecido coinciden con los que ingresamos en
    # el formulario de carga
    mov = movs_dia[0]
    importe_localizado = float_format(valores["importe"])
    cuenta_mov = mov.encontrar_elemento("class_td_cta_entrada", By.CLASS_NAME).text

    assert mov.encontrar_elemento("class_td_concepto", By.CLASS_NAME).text == valores["concepto"]
    assert mov.encontrar_elemento(f"class_td_importe", By.CLASS_NAME).text == \
        importe_localizado
    assert cuenta_mov == cuenta.nombre

    # El saldo de la cuenta sobre la que se realizó el movimiento y el saldo
    # general de la página reflejan el cambio provocado por el nuevo movimiento
    saldo_localizado = float_format(saldo + valores["importe"])
    saldo_gral_localizado = float_format(saldo_gral + valores["importe"])
    assert browser.esperar_saldo_en_moneda_de_cuenta(cuenta.sk).text == saldo_localizado
    assert \
        browser.encontrar_elemento('id_importe_saldo_gral').text == \
        saldo_gral_localizado

    # Si al cargar un nuevo movimiento pulsamos el botón "Guardar y agregar",
    # se guarda el movimiento pero en vez de volver a la página anterior, se
    # vuelve a abrir la página de carga de movimientos.
    browser.ir_a_pag(reverse("mov_nuevo"))
    browser.completar_form(boton="id_btn_gya", **valores)

    assert_exists(sk=f"{valores['fecha'].replace('-','')}01", cls=Movimiento)
    browser.assert_url(reverse("mov_nuevo"))


def test_cuentas_acumulativas_no_aparecen_entre_las_opciones_de_cuenta(
        browser, cuenta, cuenta_acumulativa):
    browser.ir_a_pag(reverse('mov_nuevo'))
    opciones_ce = browser.opciones_de_campo("cta_entrada")
    opciones_cs = browser.opciones_de_campo("cta_salida")
    assert cuenta.nombre.lower() in opciones_ce
    assert cuenta.nombre.lower() in opciones_cs
    assert \
        cuenta_acumulativa.nombre.lower() not in \
        [x.lower() for x in opciones_ce]
    assert \
        cuenta_acumulativa.nombre.lower() not in \
        [x.lower() for x in opciones_cs]


def test_crear_creditos_o_devoluciones(
        browser, cuenta, cuenta_ajena, cuenta_2, cuenta_ajena_2, fecha):
    # Si generamos un movimiento entre cuentas de distintos titulares, se
    # genera un contramovimiento por el mismo importes entre cuentas
    # generadas automáticamente con los titulares invertidos

    # Completamos el form de movimiento nuevo, seleccionando cuentas de
    # titulares distintos en los campos de cuentas
    browser.crear_movimiento(
        fecha=fecha,
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
    celdas_mov = browser.dict_movimiento("Préstamo")
    contramov = browser.esperar_movimiento("concepto", "Constitución de crédito")
    celdas_contramov = browser.dict_movimiento("Constitución de crédito")

    # - los nombres de los titulares en el detalle
    assert celdas_contramov["Detalle"] == f"de {emisor.nombre} a {receptor.nombre}"

    # - el mismo importe que el movimiento creado
    assert celdas_mov["Importe"] == celdas_contramov["Importe"] == float_format(30)

    # - dos cuentas generadas automáticamente a partir de los titulares,
    #   con la cuenta del titular de la cuenta de entrada del movimiento
    #   creado como cuenta de salida, y viceversa
    assert celdas_mov["Entra en"] == cuenta.nombre
    assert celdas_mov["Sale de"] == cuenta_ajena.nombre
    assert celdas_contramov["Entra en"] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    assert celdas_contramov["Sale de"] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()

    # - a diferencia del movimiento creado manualmente, no muestra botones
    #   de editar o borrar.
    assert mov.encontrar_elemento("class_link_elim_mov", By.CLASS_NAME).text == "B"
    assert mov.encontrar_elemento("class_link_mod_mov", By.CLASS_NAME).text == "E"
    with pytest.raises(NoSuchElementException):
        contramov.encontrar_elemento("class_link_elim_mov", By.CLASS_NAME)
    with pytest.raises(NoSuchElementException):
        contramov.encontrar_elemento("class_link_mod_mov", By.CLASS_NAME)

    # Si vamos a la página de detalles del titular de la cuenta de salida,
    # vemos entre sus cuentas la cuenta generada automáticamente que lo
    # muestra como acreedor, con saldo igual a {saldo}
    browser.ir_a_pag(emisor.get_absolute_url())
    link_cuenta = browser.encontrar_elemento(f"id_link_cta__{emisor.sk}-{receptor.sk}")
    saldo_cuenta = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.sk}-{receptor.sk}")
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
    celdas_contramov = browser.dict_movimiento("Aumento de crédito")
    assert celdas_contramov["Importe"] == float_format(10)
    assert celdas_contramov["Entra en"] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    assert celdas_contramov["Sale de"] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.sk}-{receptor.sk}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.sk}-{emisor.sk}")
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
    celdas_contramov = browser.dict_movimiento("Pago a cuenta de crédito")
    assert celdas_contramov["Importe"] == float_format(15)
    assert celdas_contramov["Entra en"] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()
    assert celdas_contramov["Sale de"] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.sk}-{receptor.sk}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.sk}-{emisor.sk}")
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
    celdas_contramov = browser.dict_movimiento("Pago a cuenta de crédito", 1)
    assert celdas_contramov["Importe"] == float_format(7)
    assert celdas_contramov["Entra en"] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()
    assert celdas_contramov["Sale de"] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.sk}-{receptor.sk}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.sk}-{emisor.sk}")
    assert saldo_cuenta_acreedora.text == float_format(30+10-15-7)
    assert saldo_cuenta_deudora.text == float_format(-30-10+15+7)

    # Si generamos un movimiento entre ambos titulares con importe mayor al
    # total de la deuda:
    # - el contramovimiento se genera con concepto ""
    # - las cuentas crédito cambian de nombre y de sk (deuda de receptor con emisor se convierte en
    #   préstamo de receptor a emisor y viceversa)
    browser.crear_movimiento(
        concepto="Devolución con exceso",
        importe="20",
        cta_entrada=cuenta_ajena.nombre,
        cta_salida=cuenta.nombre
    )
    celdas_contramov = browser.dict_movimiento("Pago en exceso de crédito")
    assert celdas_contramov["Importe"] == float_format(20)
    assert celdas_contramov["Entra en"] == f"préstamo de {receptor.nombre} a {emisor.nombre}".lower()
    assert celdas_contramov["Sale de"] == f"deuda de {emisor.nombre} con {receptor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.sk}-{emisor.sk}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.sk}-{receptor.sk}")
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
    celdas_contramov = browser.dict_movimiento("Cancelación de crédito")
    assert celdas_contramov["Importe"] == float_format(2)
    assert celdas_contramov["Entra en"] == f"deuda de {emisor.nombre} con {receptor.nombre}".lower()
    assert celdas_contramov["Sale de"] == f"préstamo de {receptor.nombre} a {emisor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.sk}-{receptor.sk}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.sk}-{emisor.sk}")
    assert saldo_cuenta_acreedora.text == float_format(30+10-15-7-18)
    assert saldo_cuenta_deudora.text == float_format(-30-10+15+7+18)


def test_crear_traspaso_entre_titulares_sin_deuda(browser, cuenta, cuenta_ajena, fecha):
    # Antes de empezar, tomamos los valores de los capitales mostrados en las
    # páginas de detalle de los titulares cuyas cuentas usaremos
    browser.ir_a_pag(cuenta_ajena.titular.get_absolute_url())
    capital_emisor = browser.encontrar_elemento(f"id_capital_{cuenta_ajena.titular.sk}").text
    browser.ir_a_pag(cuenta.titular.get_absolute_url())
    capital_receptor = browser.encontrar_elemento(f"id_capital_{cuenta.titular.sk}").text

    # Completamos el form de movimiento nuevo, seleccionando cuentas de
    # titulares distintos en los campos de cuentas. Cliqueamos en la casilla
    # "esgratis"
    browser.crear_movimiento(
        fecha=fecha,
        concepto="Donación",
        importe="30",
        cta_entrada=cuenta.nombre,
        cta_salida=cuenta_ajena.nombre,
        esgratis=True
    )

    # Vemos que sólo se genera el movimiento creado, sin que se genere ningún
    # movimiento automático de deuda.
    browser.esperar_movimiento("concepto", "Donación")
    with pytest.raises(NoSuchElementException):
        browser.esperar_movimiento("concepto", "Constitución de crédito")

    # Si vamos a la página de detalles del titular de la cuenta de salida
    # (emisor), vemos que entre sus cuentas no hay ninguna generada automáticamente, sólo
    # las cuentas regulares-
    browser.ir_a_pag(cuenta_ajena.titular.get_absolute_url())
    cuentas_pag = [
        x.text for x in browser.encontrar_elementos("class_link_cuenta")
    ]
    cuenta_credito = \
        f"_{cuenta_ajena.titular.sk}-{cuenta.titular.sk}".upper()
    assert \
        cuenta_credito not in cuentas_pag, \
        f"Cuenta {cuenta_credito}, que no debería existir, existe"

    # Y vemos que el capital del emisor disminuyó en un importe igual al del
    # movimiento que creamos
    assert capital_emisor == float_format(cuenta_ajena.titular.capital() + 30)

    # Lo mismo con el titular de la cuenta de entrada.
    browser.ir_a_pag(cuenta.titular.get_absolute_url())
    cuentas_pag = [
        x.text for x in browser.encontrar_elementos("class_link_cuenta")
    ]
    cuenta_credito = \
        f"_{cuenta.titular.sk}-{cuenta_ajena.titular.sk}".upper()
    assert \
        cuenta_credito not in cuentas_pag, \
        f"Cuenta {cuenta_credito}, que no debería existir, existe"
    assert capital_receptor == float_format(cuenta.titular.capital() - 30)


@pytest.mark.parametrize('cta_entrada, cta_salida, moneda', [
    ('cuenta_en_dolares', 'none', 'euro'),
    ('none', 'cuenta_en_euros', 'dolar'),
    ('cuenta_en_dolares', 'cuenta_con_saldo_en_dolares', 'peso'),
])
def test_crear_movimiento_con_cuenta_en_moneda_no_base(
        browser, cta_entrada, cta_salida, moneda, fecha, importe, request):
    ce = request.getfixturevalue(cta_entrada)
    cs = request.getfixturevalue(cta_salida)
    moneda = request.getfixturevalue(moneda)
    moneda_correcta = ce.moneda if ce else cs.moneda
    browser.ir_a_pag()

    # Dadas dos cuentas en una misma moneda
    saldo_base_original_ce = format_float(browser.esperar_saldo_en_moneda_de_cuenta(ce.sk).text) if ce else None
    saldo_base_original_cs = format_float(browser.esperar_saldo_en_moneda_de_cuenta(cs.sk).text) if cs else None

    # Cuando generamos un movimiento sobre una o ambas cuentas
    browser.crear_movimiento(
        concepto='Movimiento en dólares',
        importe=str(importe),
        fecha=fecha,
        cta_entrada=ce.nombre if ce else None,
        cta_salida=cs.nombre if cs else None,
        moneda=moneda.nombre,
    )

    # Si seleccionamos para el importe una moneda distinta de la moneda de
    # la cuenta, recibimos un mensaje de error
    lista_errores = browser.encontrar_elemento("ul.errorlist", By.CSS_SELECTOR)
    assert f"El movimiento debe ser expresado en {moneda_correcta.plural}" in lista_errores.text

    # Si seleccionamos para el importe la moneda de las cuentas, se nos permite
    # completar el movimiento
    browser.completar("id_moneda", moneda_correcta.nombre)
    browser.pulsar()

    # Somos dirigidos a la página principal donde podemos ver que el saldo
    # principal de la o las cuentas cambió en el importe registrado en el movimiento,
    browser.assert_url(reverse('home'))
    if ce:
        saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(ce.sk)
        assert saldo_base.text == float_format(saldo_base_original_ce + importe)
    if cs:
        saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cs.sk)
        assert saldo_base.text == float_format(saldo_base_original_cs - importe)


@pytest.mark.parametrize('moneda, otra_moneda, cuenta_con_saldo_en_moneda, cotizacion_mov', [
    ('euro', 'dolar', 'cuenta_con_saldo_en_euros', '1.1'),
    ('dolar', 'euro', 'cuenta_con_saldo_en_dolares', '0.9')
])
def test_crear_traspaso_entre_cuentas_en_distinta_moneda(
        browser, moneda, otra_moneda, cuenta_con_saldo_en_moneda, cotizacion_mov, peso, fecha, request):
    moneda_mov = request.getfixturevalue(moneda)
    otra_moneda = request.getfixturevalue(otra_moneda)
    cuenta_con_saldo_en_moneda_mov = request.getfixturevalue(cuenta_con_saldo_en_moneda)
    cuenta_con_saldo_en_otra_moneda = request.getfixturevalue(
        el_que_no_es(
            cuenta_con_saldo_en_moneda,
            "cuenta_con_saldo_en_euros",
            "cuenta_con_saldo_en_dolares"
        )
    )
    browser.ir_a_pag()

    # Dadas dos cuentas en monedas distintas
    saldo_base_original_csmm = format_float(
        browser.esperar_saldo_en_moneda_de_cuenta(
            cuenta_con_saldo_en_moneda_mov.sk
        ).text
    )
    saldo_base_original_csom = format_float(
        browser.esperar_saldo_en_moneda_de_cuenta(
            cuenta_con_saldo_en_otra_moneda.sk
        ).text
    )

    # Cuando generamos un movimiento de traspaso entre ambas cuentas
    browser.crear_movimiento(
        concepto=f"Compra de {moneda_mov.plural} con {otra_moneda.plural}",
        importe="20",
        fecha=fecha,
        cta_entrada=cuenta_con_saldo_en_moneda_mov.nombre,
        cta_salida=cuenta_con_saldo_en_otra_moneda.nombre,
        moneda=peso.nombre,
        cotizacion=cotizacion_mov
    )

    # Si seleccionamos para el importe una moneda distinta de la moneda de
    # la cuenta, recibimos un mensaje de error
    lista_errores = browser.encontrar_elemento("ul.errorlist", By.CSS_SELECTOR)
    assert f"El movimiento debe ser expresado en {moneda_mov.plural} o {otra_moneda.plural}" in lista_errores.text

    # Si seleccionamos para el importe la moneda de alguna de las cuentas, se nos permite
    # completar el movimiento
    browser.completar("id_moneda", moneda_mov.nombre)
    browser.pulsar()

    # Somos dirigidos a la página principal donde podemos ver que el saldo
    # principal de la o las cuentas cambió en el importe registrado en el movimiento,
    browser.assert_url(reverse('home'))
    importe_en_moneda_mov = 20
    importe_en_otra_moneda = round(20 * float(cotizacion_mov), 2)
    saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cuenta_con_saldo_en_moneda_mov.sk)
    assert saldo_base.text == float_format(saldo_base_original_csmm + importe_en_moneda_mov)
    saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cuenta_con_saldo_en_otra_moneda.sk)
    assert saldo_base.text == float_format(saldo_base_original_csom - importe_en_otra_moneda)


def test_crear_traspaso_entre_cuentas_en_distinta_moneda_con_una_cotizacion_anterior_a_la_actual(
        browser, cuenta_con_saldo_en_euros, cuenta_con_saldo_en_dolares, dolar, euro,
        fecha, cotizacion_dolar, cotizacion_posterior_dolar, cotizacion_posterior_euro
):
    browser.ir_a_pag()

    # Dadas dos cuentas en monedas distintas
    saldo_base_original_ce = format_float(
        browser.esperar_saldo_en_moneda_de_cuenta(
            cuenta_con_saldo_en_euros.sk
        ).text
    )
    saldo_base_original_cs = format_float(
        browser.esperar_saldo_en_moneda_de_cuenta(
            cuenta_con_saldo_en_dolares.sk
        ).text
    )

    # Cuando generamos un movimiento de traspaso entre ambas cuentas
    # y la fecha de ese movimiento es anterior a la de la última cotización
    # de las cuentas
    browser.crear_movimiento(
        concepto='Compra de euros con dólares ólares',
        importe="20",
        fecha=fecha,
        cta_entrada=cuenta_con_saldo_en_euros.nombre,
        cta_salida=cuenta_con_saldo_en_dolares.nombre,
        moneda=dolar.nombre,
    )

    # Somos dirigidos a la página principal donde podemos ver que el saldo
    # principal de la o las cuentas cambió en el importe registrado en el movimiento,
    browser.assert_url(reverse('home'))
    importe_en_euros = round(20 * dolar.cotizacion_en_al(euro, fecha, compra=False), 2)
    importe_en_dolares = 20
    saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cuenta_con_saldo_en_euros.sk)
    assert saldo_base.text == float_format(saldo_base_original_ce + importe_en_euros)
    saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cuenta_con_saldo_en_dolares.sk)
    assert saldo_base.text == float_format(saldo_base_original_cs - importe_en_dolares)


def test_modificar_movimiento(browser, entrada, salida_posterior, cuenta_2):
    # Las modificaciones hechas mediante el formulario de movimiento se ven
    # reflejadas en el movimiento que se muestra en la página principal
    browser.ir_a_pag(entrada.get_edit_url())

    # En todos los campos del formulario aparece el valor del campo correspondiente del movimiento:
    browser.controlar_modelform(instance=entrada)
    esgratis = browser.encontrar_elemento("id_esgratis")
    assert esgratis.get_attribute("value") == "on" if entrada.id_contramov is None else "off"

    # En el caso de modificar movimiento, no aparece el botón "Guardar y agregar"
    browser.no_encontrar_elemento("id_btn_gya")

    browser.completar_form(
        concepto='Movimiento con concepto modificado',
        cta_entrada='cuenta 2',
        importe='124',
    )
    browser.assert_url(reverse('home'))
    concepto_movimiento = browser.encontrar_elemento(f"id_link_mov_{entrada.sk}").text.strip()
    assert concepto_movimiento == "Movimiento con concepto modificado"
    fila_movimiento = browser.encontrar_elemento(f"id_row_mov_{entrada.sk}")
    cuenta_movimiento = fila_movimiento.encontrar_elemento('class_td_cta_entrada', By.CLASS_NAME).text.strip()
    assert cuenta_movimiento == cuenta_2.nombre
    importe_movimiento = fila_movimiento.encontrar_elemento('class_td_importe', By.CLASS_NAME).text.strip()
    assert importe_movimiento == "124,00"


def test_convertir_entrada_en_traspaso_entre_titulares(browser, entrada, cuenta_ajena):
    # Cuando se agrega a un movimiento de entrada una cuenta ajena como cuenta
    # de salida, se genera un contramovimiento en el mismo día que el movimiento
    browser.ir_a_pag()
    dia = browser.esperar_dia(entrada.fecha)
    cantidad_movimientos = len(dia.encontrar_elementos('class_row_mov'))

    browser.ir_a_pag(entrada.get_edit_url())
    browser.completar_form(cta_salida=cuenta_ajena.nombre, esgratis='False')

    dia = browser.esperar_dia(entrada.fecha)
    assert len(dia.encontrar_elementos('class_row_mov')) == cantidad_movimientos + 1
    mov_nuevo = dia.encontrar_elementos('class_row_mov', By.CLASS_NAME)[1]
    assert mov_nuevo.encontrar_elemento('class_td_concepto', By.CLASS_NAME).text == 'Constitución de crédito'


@pytest.mark.parametrize("origen", ["/", "/diario/t/titular/", "/diario/c/c/", "/diario/m/", "/diario/cm/c/"])
@pytest.mark.parametrize("destino", ["#id_link_mov_nuevo", "#id_row_mov_xxx .class_link_mod_mov"])
def test_crear_o_modificar_movimiento_vuelve_a_la_pagina_desde_la_que_se_lo_invoco(
        browser, origen, destino, valores, titular, cuenta, entrada, entrada_anterior, entrada_cuenta_ajena):
    if "m/" in origen:
        origen = f"{origen}{entrada_anterior.sk}"
    if destino == "#id_row_mov_xxx .class_link_mod_mov":
        destino = destino.replace("xxx", entrada.sk)

    browser.ir_a_pag(origen)
    browser.pulsar(destino, By.CSS_SELECTOR)
    browser.completar_form(**valores)
    browser.assert_url(origen)


@pytest.mark.parametrize("origen", [None, "cuenta", "titular"])
@pytest.mark.parametrize("destino", ["#id_link_mov_nuevo", "#id_row_mov_xxx .class_link_mod_mov"])
def test_crear_o_modificar_movimiento_desde_pagina_anterior_redirige_a_esa_pagina_con_el_ultimo_movimiento_seleccionado(
        browser, mas_de_7_dias, entrada_temprana, origen, destino, valores, request):
    if origen:
        ente = request.getfixturevalue(origen)
        url_origen = ente.get_absolute_url()
        dias = list(ente.dias())
    else:
        ente = None
        url_origen = reverse("home")
        dias = list(mas_de_7_dias)
    movimiento = dias[-8].movimientos.last()
    url_final = movimiento.get_url(ente)
    if destino == "#id_row_mov_xxx .class_link_mod_mov":
        mov = dias[0].movimientos.first()
        destino = destino.replace("xxx", mov.sk)
        valores.pop("fecha")

    browser.ir_a_pag(url_origen + "?page=2")
    browser.pulsar(destino, By.CSS_SELECTOR)
    browser.completar_form(**valores)
    browser.assert_url(url_final + "?page=2")

def test_eliminar_movimiento(browser, entrada, salida):
    # Cuando se elimina un movimiento desaparece de la página principal
    concepto = entrada.concepto
    browser.ir_a_pag(entrada.get_delete_url())
    browser.pulsar('id_btn_confirm')
    browser.assert_url(reverse('home'))
    conceptos = [x.text.strip() for x in browser.encontrar_elementos('class_link_movimiento')]
    assert concepto not in conceptos


@pytest.mark.parametrize("origen", ["/", "/diario/t/titular/", "/diario/c/c/", "/diario/m/", "/diario/cm/c/"])
def test_eliminar_movimiento_vuelve_a_la_pagina_desde_que_se_lo_invoco(
        browser, origen, titular, cuenta, entrada, entrada_anterior, entrada_cuenta_ajena):
    if "m/" in origen:
        origen = f"{origen}{entrada_anterior.sk}"
    browser.ir_a_pag(origen)
    browser.pulsar(f"#id_row_mov_{entrada.sk} .class_link_elim_mov", By.CSS_SELECTOR)
    browser.pulsar("id_btn_confirm")
    browser.assert_url(origen)


@pytest.mark.parametrize("origen", [None, "cuenta", "titular"])
def test_eliminar_movimiento_desde_pagina_posterior_redirige_a_esa_pagina_con_el_ultimo_movimiento_seleccionado(
        browser, mas_de_7_dias, fecha_inicial, cuenta, origen, request):
    if origen:
        ente = request.getfixturevalue(origen)
        url_origen = ente.get_absolute_url()
        dias = list(ente.dias())
    else:
        ente = None
        url_origen = reverse("home")
        dias = list(mas_de_7_dias)
    movimiento = dias[-8].movimientos.last()
    url_destino = movimiento.get_url(ente)
    mov_a_eliminar = dias[0].movimientos.first()

    browser.ir_a_pag(url_origen + "?page=2")
    browser.pulsar(f"#id_row_mov_{mov_a_eliminar.sk} .class_link_elim_mov", By.CSS_SELECTOR)
    browser.pulsar("id_btn_confirm")

    browser.assert_url(url_destino + "?page=2")
