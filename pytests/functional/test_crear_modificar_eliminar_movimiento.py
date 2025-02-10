from datetime import date
from typing import List

import pytest
from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from utils.numeros import float_format, format_float
from utils.varios import el_que_no_es
from vvsteps.driver import MiWebElement


def textos_hijos(elemento: MiWebElement, tag_subelem: str) -> List[str]:
    return [x.text for x in elemento.esperar_elementos(tag_subelem, By.TAG_NAME)]


def test_crear_movimiento(browser, cuenta, dia, dia_posterior):
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

    # El campo "fecha" del formulario tiene la fecha del último día como valor por
    # defecto
    assert \
        form_mov.esperar_elemento("id_fecha").get_attribute("value") == \
        dia_posterior.fecha.strftime('%Y-%m-%d')

    # Cargamos los valores necesarios para generar un movimiento nuevo
    browser.completar_form(**valores)

    # En la lista de movimientos del día, aparece un movimiento nuevo
    dia = browser.esperar_dia(date(2010, 12, 5))
    movs_dia = dia.esperar_elementos("class_row_mov")
    assert len(movs_dia) == 1

    # Los valores del movimiento aparecido coinciden con los que ingresamos en
    # el formulario de carga
    mov = movs_dia[0]
    importe_localizado = float_format(valores["importe"])
    cuenta_mov = mov.esperar_elemento("class_td_cta_entrada", By.CLASS_NAME).text

    assert mov.esperar_elemento("class_td_concepto", By.CLASS_NAME).text == valores["concepto"]
    assert mov.esperar_elemento(f"class_td_importe", By.CLASS_NAME).text == \
        importe_localizado
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
    contramov = browser.esperar_movimiento("concepto", "Constitución de crédito")
    celdas_mov = textos_hijos(mov, "td")
    celdas_contramov = textos_hijos(contramov, "td")

    # - los nombres de los titulares en el detalle
    assert celdas_contramov[2] == f"préstamo de {emisor.nombre.lower()} a {receptor.nombre.lower()}"

    # - el mismo importe que el movimiento creado
    assert celdas_mov[4] == celdas_contramov[4] == float_format(30)

    # - dos cuentas generadas automáticamente a partir de los titulares,
    #   con la cuenta del titular de la cuenta de entrada del movimiento
    #   creado como cuenta de salida, y viceversa
    assert celdas_mov[2] == cuenta.nombre
    assert celdas_mov[3] == cuenta_ajena.nombre
    assert celdas_contramov[2] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    assert celdas_contramov[3] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()

    # - a diferencia del movimiento creado manualmente, no muestra botones
    #   de editar o borrar.
    assert mov.esperar_elemento("class_link_elim_mov", By.CLASS_NAME).text == "B"
    assert mov.esperar_elemento("class_link_mod_mov", By.CLASS_NAME).text == "E"
    with pytest.raises(NoSuchElementException):
        contramov.esperar_elemento("class_link_elim_mov", By.CLASS_NAME)
    with pytest.raises(NoSuchElementException):
        contramov.esperar_elemento("class_link_mod_mov", By.CLASS_NAME)

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
    assert celdas_contramov[4] == float_format(10)
    assert celdas_contramov[2] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
    assert celdas_contramov[3] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()
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
    assert celdas_contramov[4] == float_format(15)
    assert celdas_contramov[2] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()
    assert celdas_contramov[3] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
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
    contramov = browser.esperar_movimientos("concepto", "Pago a cuenta de crédito")[1]
    celdas_contramov = textos_hijos(contramov, "td")
    assert celdas_contramov[4] == float_format(7)
    assert celdas_contramov[2] == f"deuda de {receptor.nombre} con {emisor.nombre}".lower()
    assert celdas_contramov[3] == f"préstamo de {emisor.nombre} a {receptor.nombre}".lower()
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
    assert celdas_contramov[4] == float_format(20)
    assert celdas_contramov[2] == f"préstamo de {receptor.nombre} a {emisor.nombre}".lower()
    assert celdas_contramov[3] == f"deuda de {emisor.nombre} con {receptor.nombre}".lower()
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
    assert celdas_contramov[4] == float_format(2)
    assert celdas_contramov[2] == f"deuda de {emisor.nombre} con {receptor.nombre}".lower()
    assert celdas_contramov[3] == f"préstamo de {receptor.nombre} a {emisor.nombre}".lower()
    saldo_cuenta_acreedora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{emisor.titname}-{receptor.titname}")
    saldo_cuenta_deudora = browser.esperar_saldo_en_moneda_de_cuenta(f"_{receptor.titname}-{emisor.titname}")
    assert saldo_cuenta_acreedora.text == float_format(30+10-15-7-18)
    assert saldo_cuenta_deudora.text == float_format(-30-10+15+7+18)


def test_crear_traspaso_entre_titulares_sin_deuda(browser, cuenta, cuenta_ajena, fecha):
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
        fecha=fecha,
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
    saldo_base_original_ce = format_float(browser.esperar_saldo_en_moneda_de_cuenta(ce.slug).text) if ce else None
    saldo_base_original_cs = format_float(browser.esperar_saldo_en_moneda_de_cuenta(cs.slug).text) if cs else None

    # Cuando generamos un movimiento sobre una o ambas cuentas
    browser.crear_movimiento(
        concepto='Movimiento en dólares',
        importe=str(importe),
        fecha=fecha,
        cta_entrada=ce.nombre if ce else None,
        cta_salida= cs.nombre if cs else None,
        moneda=moneda.nombre,
    )

    # Si seleccionamos para el importe una moneda distinta de la moneda de
    # la cuenta, recibimos un mensaje de error
    lista_errores = browser.esperar_elemento("ul.errorlist", By.CSS_SELECTOR)
    assert f"El movimiento debe ser expresado en {moneda_correcta.plural}" in lista_errores.text

    # Si seleccionamos para el importe la moneda de las cuentas, se nos permite
    # completar el movimiento
    browser.completar("id_moneda", moneda_correcta.nombre)
    browser.pulsar()

    # Somos dirigidos a la página principal donde podemos ver que el saldo
    # principal de la o las cuentas cambió en el importe registrado en el movimiento,
    browser.assert_url(reverse('home'))
    if ce:
        saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(ce.slug)
        assert saldo_base.text == float_format(saldo_base_original_ce + importe)
    if cs:
        saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cs.slug)
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
            cuenta_con_saldo_en_moneda_mov.slug
        ).text
    )
    saldo_base_original_csom = format_float(
        browser.esperar_saldo_en_moneda_de_cuenta(
            cuenta_con_saldo_en_otra_moneda.slug
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
    lista_errores = browser.esperar_elemento("ul.errorlist", By.CSS_SELECTOR)
    assert f"El movimiento debe ser expresado en {moneda_mov.plural} o {otra_moneda.plural}" in lista_errores.text

    # Si seleccionamos para el importe la moneda de alguna de las cuentas, se nos permite
    # completar el movimiento
    browser.completar("id_moneda", moneda_mov.nombre)
    browser.pulsar()

    # Somos dirigidos a la página principal donde podemos ver que el saldo
    # principal de la o las cuentas cambió en el importe registrado en el movimiento,
    browser.assert_url(reverse('home'))
    importe_en_moneda_mov = 20
    importe_en_otra_moneda = round(20 / float(cotizacion_mov), 2)
    saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cuenta_con_saldo_en_moneda_mov.slug)
    assert saldo_base.text == float_format(saldo_base_original_csmm + importe_en_moneda_mov)
    saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cuenta_con_saldo_en_otra_moneda.slug)
    assert saldo_base.text == float_format(saldo_base_original_csom - importe_en_otra_moneda)


def test_crear_traspaso_entre_cuentas_en_distinta_moneda_con_una_cotizacion_anterior_a_la_actual(
        browser, cuenta_con_saldo_en_euros, cuenta_con_saldo_en_dolares, dolar, euro,
        fecha, cotizacion, cotizacion_posterior, cotizacion_posterior_euro
):
    browser.ir_a_pag()

    # Dadas dos cuentas en monedas distintas
    saldo_base_original_ce = format_float(
        browser.esperar_saldo_en_moneda_de_cuenta(
            cuenta_con_saldo_en_euros.slug
        ).text
    )
    saldo_base_original_cs = format_float(
        browser.esperar_saldo_en_moneda_de_cuenta(
            cuenta_con_saldo_en_dolares.slug
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
    importe_en_euros = round(20 / euro.cotizacion_en_al(dolar, fecha, compra=False), 2)
    importe_en_dolares = 20
    saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cuenta_con_saldo_en_euros.slug)
    assert saldo_base.text == float_format(saldo_base_original_ce + importe_en_euros)
    saldo_base = browser.esperar_saldo_en_moneda_de_cuenta(cuenta_con_saldo_en_dolares.slug)
    assert saldo_base.text == float_format(saldo_base_original_cs - importe_en_dolares)


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
    # de salida, se genera un contramovimiento en el mismo día que el movimiento
    browser.ir_a_pag()
    dia = browser.esperar_dia(entrada.fecha)
    cantidad_movimientos = len(dia.esperar_elementos('class_row_mov'))

    browser.ir_a_pag(reverse('mov_mod', args=[entrada.pk]))
    browser.completar_form(cta_salida=cuenta_ajena.nombre, esgratis='False')

    dia = browser.esperar_dia(entrada.fecha)
    assert len(dia.esperar_elementos('class_row_mov')) == cantidad_movimientos + 1
    mov_nuevo = dia.esperar_elementos('class_row_mov', By.CLASS_NAME)[1]
    assert mov_nuevo.esperar_elemento('class_td_concepto', By.CLASS_NAME).text == 'Constitución de crédito'


def test_eliminar_movimiento(browser, entrada, salida):
    # Cuando se elimina un movimiento desaparece de la página principal
    concepto = entrada.concepto
    browser.ir_a_pag(reverse('mov_elim', args=[entrada.pk]))
    browser.pulsar('id_btn_confirm')
    browser.assert_url(reverse('home'))
    conceptos = [x.text.strip() for x in browser.esperar_elementos('class_link_movimiento')]
    assert concepto not in conceptos
