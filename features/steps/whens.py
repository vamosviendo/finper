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

from consts import BYS, ORDINALES, NOMBRES_URL
from diario.models import Cuenta, Movimiento
from utils.archivos import fijar_mtime


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


@when('agrego un movimiento con campos')
def agregar_movimiento(context):
    for fila in context.table:
        context.browser.completar(f"id_{fila['nombre']}", fila['valor'])
    context.browser.pulsar()


@when('cliqueo en el {orden} botón de {atributo} "{texto}"')
def cliquear_en(context, orden, atributo, texto):
    atr = BYS.get(atributo, By.LINK_TEXT)
    context.browser.esperar_elementos(texto, atr)[ORDINALES[orden]].click()


@when('cliqueo en el botón de {atributo} "{texto}"')
def cliquear_en(context, atributo, texto):
    context.execute_steps(
        f'Cuando cliqueo en el primer botón de {atributo} "{texto}"'
    )


@when('cliqueo en el botón "{texto}"')
def cliquear_en_el_boton(context, texto):
    context.execute_steps(
        f'Cuando cliqueo en el botón de contenido "{texto}"'
    )


@when('cliqueo en el botón')
def cliquear_en(context):
    context.execute_steps(
        'Cuando cliqueo en el botón de id "id_btn_submit"'
    )


@when('completo el form de dividir cuenta con estos valores')
def completar_form_dividir_cuenta(context):
    for ind, fila in enumerate(context.table):
        context.browser.completar(f'id_form-{ind}-nombre', fila['nombre'])
        context.browser.completar(f'id_form-{ind}-slug', fila['slug'])
        context.browser.completar(f'id_form-{ind}-saldo', fila['saldo'])
    context.browser.pulsar()


@when('entro en la cuenta "{nombre}"')
def entrar_en_cuenta(context, nombre):
    nombre = nombre.lower()
    slug = Cuenta.tomar(nombre=nombre).slug
    context.browser.esperar_elemento(nombre, By.LINK_TEXT).click()
    context.test.assertEqual(
        context.browser.esperar_elemento(
            f'#id_div_cta_{slug} .class_nombre_cuenta_main',
            By.CSS_SELECTOR
        ).text,
        nombre
    )


@when('introduzco un error de {importe} pesos en el saldo de la cuenta "{nombre}"')
def introducir_saldo_erroneo(context, importe, nombre):
    context.execute_steps(
        f'Dado un error de {importe} pesos en el saldo de la cuenta "{nombre}"'
    )


@when('{accion} "{texto}" en el campo "{campo}"') # acción=escribo, selecciono
def completar_campo(context, accion, texto, campo):
    if accion == 'escribo':
        tipo = 'input'
    elif accion == 'selecciono':
        texto = '---------' if texto == 'nada' else texto
        tipo = 'select'
    else:
        raise ValueError('La acción debe ser "escribo" o "selecciono')
    context.browser.completar(f'{tipo}[name="{campo}"]', texto, By.CSS_SELECTOR)


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


@when('voy a la página principal')
def ir_a_pag_principal(context):
    context.browser.get(context.get_url('/'))


@when('voy a la página principal sin que haya cambiado el día')
def ir_a_pag_principal(context):
    context.execute_steps('Cuando voy a la página principal')


@when('voy a la página "{pag}" del último movimiento')
def ir_a_pag_ult_mov(context, pag):
    nombre = NOMBRES_URL.get(pag) or pag
    context.browser.get(
        context.get_url(
            reverse(nombre, args=[Movimiento.objects.last().pk])
        )
    )


@when('voy a la página "{pag}"')
def ir_a_pag(context, pag):
    nombre = NOMBRES_URL.get(pag) or pag
    context.browser.get(context.get_url(reverse(nombre)))


@when('me detengo')
def detenerse(context):
    input()
