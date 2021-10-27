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
from django.urls import reverse
from selenium.webdriver.common.by import By

from consts import NOMBRES_URL
from diario.models import Cuenta, Movimiento
from utils.archivos import fijar_mtime


# ACCIONES DE TITULAR

@when('cliqueo en el titular "{nombre}"')
def cliquear_en_titular(context, nombre):
    context.execute_steps(f'''
        Entonces veo un "section" de id "titulares"
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
    context.browser.esperar_elemento(nombre, By.LINK_TEXT).click()
    context.test.assertEqual(
        context.browser.esperar_elemento('id_div_titulo_pag',).text,
        nombre
    )


@when('cliqueo en el botón "{boton}" de la cuenta "{cuenta}"')
def cliquear_en_boton_cuenta(context, boton, cuenta):
    cuenta_pag = context.browser.esperar_elemento(
        f'id_div_cta_{Cuenta.tomar(nombre=cuenta).slug}')
    cuenta_pag.find_element_by_link_text(boton).click()


@when('completo el form de dividir cuenta con estos valores')
def completar_form_dividir_cuenta(context):
    for ind, fila in enumerate(context.table):
        context.browser.completar(f'id_form-{ind}-nombre', fila['nombre'])
        context.browser.completar(f'id_form-{ind}-slug', fila['slug'])
        if fila.get('saldo') is not None:
            context.browser.completar(f'id_form-{ind}-saldo', fila['saldo'])
    context.browser.pulsar()


@when('completo el form de agregar subcuenta con estos valores')
def completar_form_agregar_subcuenta(context):
    context.browser.completar('id_nombre', context.table[0]['nombre'])
    context.browser.completar('id_slug', context.table[0]['slug'])
    context.browser.pulsar()


@when('introduzco un error de {importe} pesos en el saldo de la cuenta "{nombre}"')
def introducir_saldo_erroneo(context, importe, nombre):
    context.execute_steps(
        f'Dado un error de {importe} pesos en el saldo de la cuenta "{nombre}"'
    )


# ACCIONES DE MOVIMIENTO

@when('agrego un movimiento con campos')
def agregar_movimiento(context):
    for fila in context.table:
        context.browser.completar(f"id_{fila['nombre']}", fila['valor'])
    context.browser.pulsar()


@when('voy a la página "{pag}" del último movimiento')
def ir_a_pag_ult_mov(context, pag):
    nombre = NOMBRES_URL.get(pag) or pag
    context.execute_steps(
        f'Cuando voy a la página "{nombre}" '
        f'con el argumento "{Movimiento.ultime().pk}"'
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