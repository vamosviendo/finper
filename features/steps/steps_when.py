""" Las implementaciones deben ir de lo más particular a lo más general.
    Por ejemplo:
        @when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
        @when('agrego una cuenta con nombre "{nombre}"')
        @when('agrego una cuenta')
"""
import datetime
from pathlib import Path
from unittest.mock import patch

from behave import when
from selenium.webdriver.common.by import By

from consts import NOMBRES_URL
from diario.models import Cuenta, Movimiento, Titular
from utils.archivos import fijar_mtime
from vvselenium.helpers import table_to_str

"""Steps en el archivo:
@when('cliqueo en el titular "{nombre}"')
@when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
@when('agrego una cuenta con nombre "{nombre}"')
@when('agrego una cuenta')
@when('entro en la cuenta "{nombre}"')
@when('cliqueo en el botón "{boton}" de la cuenta "{cuenta}"')
@when('cliqueo en el botón "{boton}" del titular "{titular}"')

@when('completo el form de dividir cuenta con estos valores')
@when('completo el form de agregar subcuenta con estos valores')

@when('introduzco un error de {importe} pesos en el saldo de la cuenta "{nombre}"')

@when('agrego un movimiento con campos')
@when('genero un movimiento con los siguientes valores')
@when('genero un movimiento "{concepto}" de {importe} pesos de "{cta_salida}" a "{cta_entrada}"'

@when('voy a la página "{pag}" del {orden} movimiento')
@when('voy a la página "{pag}" del movimiento de concepto "{concepto}"')
@when('voy a la página principal por primera vez en el día')
@when('voy a la página principal sin que haya cambiado el día')
@when('voy a la página "{pag}" de la cuenta "{coso}"')
@when('voy a la página "{pag}" del titular "{coso}"')
"""


# ACCIONES DE TITULAR

@when('cliqueo en el titular "{nombre}"')
def cliquear_en_titular(context, nombre):
    context.execute_steps(f'''
        Entonces veo un "grid" de id "titulares"
        Cuando cliqueo en el link de texto "{nombre}"
    ''')


# ACCIONES DE CUENTA

@when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
def agregar_cuenta(context, nombre, slug):
    context.browser.completar('id_nombre', nombre)
    context.browser.completar('id_slug', slug)
    context.browser.pulsar()


@when('agrego una cuenta con nombre "{nombre}"')
def agregar_cuenta(context, nombre):
    context.execute_steps(
        f'Cuando agrego una cuenta con nombre "{nombre}" y slug "{nombre[:1]}"'
    )


@when('agrego una cuenta')
def agregar_cuenta(context):
    context.execute_steps('Cuando agrego una cuenta con nombre "Efectivo"')


@when('entro en la cuenta "{nombre}"')
def entrar_en_cuenta(context, nombre):
    nombre = nombre.lower()
    slug = Cuenta.tomar(nombre=nombre).slug.upper()
    context.browser.esperar_elemento(slug, By.LINK_TEXT).click()
    context.test.assertEqual(
        context.browser.esperar_elemento('id_div_titulo_pag',).text,
        nombre
    )


@when('cliqueo en el botón "{boton}" de la cuenta "{cuenta}"')
def cliquear_en_boton_cuenta(context, boton, cuenta):
    cuenta_pag = context.browser.esperar_elemento(
        f'id_div_cta_{Cuenta.tomar(nombre=cuenta.lower()).slug}')
    cuenta_pag.find_element_by_link_text(boton).click()


@when('cliqueo en el botón "{boton}" del titular "{titular}"')
def cliquear_en_boton_titular(context, boton, titular):
    titular_pag = context.browser.esperar_elemento(
        f'id_div_titular_{Titular.tomar(nombre=titular).titname}')
    titular_pag.find_element_by_link_text(boton).click()


@when('completo el form de dividir cuenta con estos valores')
def completar_form_dividir_cuenta(context):
    for ind, fila in enumerate(context.table):
        for campo in fila.headings:
            if fila[campo]:
                context.browser.completar(
                    f'id_form-{ind}-{campo}', fila[campo])

    context.browser.pulsar()


@when('completo el form de agregar subcuenta con estos valores')
def completar_form_agregar_subcuenta(context):
    valores = context.table[0]
    for campo in valores.headings:
        context.browser.completar(f'id_{campo}', valores[campo])

    context.browser.pulsar()


@when('introduzco un error de {importe} pesos en el saldo de la cuenta "{nombre}"')
def introducir_saldo_erroneo(context, importe, nombre):
    context.execute_steps(
        f'Dado un error de {importe} pesos en el saldo de la cuenta "{nombre}"'
    )


# ACCIONES DE MOVIMIENTO

@when('agrego un movimiento con campos')
def agregar_movimiento(context):
    context.execute_steps(
        f'Cuando completo y envío formulario con los siguientes valores'
        f'\n{table_to_str(context.table)}'
    )


@when('genero movimientos con los siguientes valores')
def generar_movimiento(context):
    context.execute_steps(
        f'Dados movimientos con los siguientes valores'
        f'\n{table_to_str(context.table)}'
    )


@when('genero un movimiento con los siguientes valores')
def generar_movimiento(context):
    context.execute_steps(
        f'Cuando genero movimientos con los siguientes valores'
        f'\n{table_to_str((context.table))}'
    )


@when('genero un movimiento "{concepto}" de {importe} pesos '
      'de "{cta_salida}" a "{cta_entrada}"')
def generar_movimiento(context, concepto, importe, cta_salida, cta_entrada):
    context.execute_steps(f'''
        Cuando voy a la página "mov_nuevo"
        Y agrego un movimiento con campos
            | nombre      | valor         |
            | concepto    | {concepto}    |
            | importe     | {importe}     |
            | cta_entrada | {cta_entrada} |
            | cta_salida  | {cta_salida}  |
    ''')


@when('voy a la página "{pag}" del {orden} movimiento')
def ir_a_pag_ult_mov(context, pag, orden):
    if orden in ["último", "ultimo"]:
        mov_pk = Movimiento.ultime().pk
    elif orden == "primer":
        mov_pk = Movimiento.primere().pk
    else:
        raise ValueError(f'Opción "{orden}" no implementada')

    nombre = NOMBRES_URL.get(pag) or pag
    context.execute_steps(
        f'Cuando voy a la página "{nombre}" '
        f'con el argumento "{mov_pk}"'
    )


@when('voy a la página "{pag}" del movimiento de concepto "{concepto}"')
def ir_a_pag_mov(context, pag, concepto):
    mov_pk = Movimiento.tomar(concepto=concepto).pk
    nombre = NOMBRES_URL.get(pag, pag)
    context.execute_steps(
        f'Cuando voy a la página "{nombre}" '
        f'con el argumento "{mov_pk}"'
    )


# NAVEGACIÓN

@when('voy a la página principal por primera vez en el día')
def ir_a_pag_principal(context):
    fecha = datetime.date(2021, 4, 4)

    class FalsaFecha(datetime.date):
        @classmethod
        def today(cls):
            return fecha

    patcherf = patch('datetime.date', FalsaFecha)
    patcherf.start()

    hoy = Path('hoy.mark')
    ayer = hoy.rename('ayer.mark')
    hoy.touch()
    fijar_mtime(hoy, datetime.datetime(2021, 4, 4))

    fecha = datetime.date(2021, 4, 5)
    context.browser.get(context.get_url('/'))

    patcherf.stop()
    hoy.unlink()
    ayer.rename('hoy.mark')


@when('voy a la página principal sin que haya cambiado el día')
def ir_a_pag_principal(context):
    context.execute_steps('Cuando voy a la página principal')


@when('voy a la página "{pag}" de la cuenta "{coso}"')
def ir_a_pag_de_coso(context, pag, coso):
    cuenta = Cuenta.tomar(nombre=coso.lower()).slug
    context.execute_steps(
        f'Cuando voy a la página "{pag}" con el argumento "{cuenta}"')


# TODO: Este step y el anterior son prácticamente el mismo. Seguro que se
#       pueden unificar
@when('voy a la página "{pag}" del titular "{coso}"')
def ir_a_pag_de_coso(context, pag, coso):
    id_titular = Titular.tomar(nombre=coso).titname
    context.execute_steps(
        f'cuando voy a la página "{pag}" con el argumento "{id_titular}"'
    )
