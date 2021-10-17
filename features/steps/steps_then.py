""" Las implementaciones deben ir de lo más particular a lo más general.
    Por ejemplo:
        @when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
        @when('agrego una cuenta con nombre "{nombre}"')
        @when('agrego una cuenta')
"""
from behave import then
from selenium.webdriver.common.by import By

from consts import LISTAS_DE_ENTIDADES
from consts_base import CARDINALES
from diario.models import Cuenta
from utils import errors
from utils.fechas import hoy


# CONSTATACIONES GENERALES

@then('el saldo general es la suma de los de "{cta1}" y "{cta2}"')
def saldo_general_es(context, cta1, cta2):
    cta1 = Cuenta.tomar(nombre=cta1.lower())
    cta2 = Cuenta.tomar(nombre=cta2.lower())
    context.test.assertEqual(
        context.browser.esperar_elemento('id_div_importe_saldo_pag').text,
        f'{cta1.saldo + cta2.saldo:.2f}'
    )


@then('la grilla de cuentas está vacia')
def grilla_cuentas_vacia(context):
    cuentas = context.browser.esperar_elementos('class_div_cuenta', fail=False)
    context.test.assertEqual(len(cuentas), 0)


@then('la lista de movimientos está vacia')
def lista_movimientos_vacia(context):
    movs = context.browser.esperar_elementos('tr', By.TAG_NAME)
    context.test.assertEqual(len(movs), 1)


# CONSTATACIONES DE CUENTA

@then('la cuenta "{slug}" tiene saldo {monto}')
def cuenta_tiene_saldo(context, slug, monto):
    cuenta = context.browser.esperar_elemento(f'id_div_cta_{slug.lower()}')
    context.test.assertEqual(
        cuenta.find_element_by_class_name('class_saldo_cuenta').text,
        monto
    )


@then('las subcuentas de la página de {cuenta} tienen estos valores')
def subcuentas_de_detalle_cuenta_coinciden_con(context, cuenta):
    nombres = [e.text for e in
               context.browser.esperar_elementos('class_nombre_cuenta')]
    saldos = [e.text for e in
              context.browser.esperar_elementos('class_saldo_cuenta')]
    ids = [e.get_attribute('id') for e in
           context.browser.esperar_elementos('class_div_cuenta')]

    for i, fila in enumerate(context.table):
        context.test.assertEqual(
            ids[i], f"id_div_cta_{fila['slug']}",
            f"La id id_div_cta_{fila['slug']} no coincide con {ids[i]}"
        )
        context.test.assertEqual(
            nombres[i], fila['nombre'].lower(),
            f"El nombre {fila['nombre']} no coincide con {nombres[i]}."
        )
        saldo = f"{float(fila['saldo']):.2f}"
        context.test.assertEqual(
            saldos[i], saldo,
            f"El saldo de {fila['nombre']} es {saldos[i]}, no {saldo}."
        )


@then('no veo una cuenta {nombre} en la grilla')
def cuenta_no_esta_en_grilla(context, nombre):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertNotIn(
        nombre.lower(),
        [x.find_element_by_class_name('class_nombre_cuenta').text
         for x in cuentas]
    )


@then('veo {x} subcuentas en la página {cuenta}')
def detalle_cuenta_tiene_subcuentas(context, cuenta, x):
    nombre_cta_main = context.browser.esperar_elemento('id_div_titulo_pag')

    context.test.assertEqual(
        nombre_cta_main.text, cuenta.lower(),
        f'La cuenta seleccionada no coincide con {cuenta}'
    )

    num_subcuentas = len(context.browser.esperar_elementos('class_div_cuenta'))
    context.test.assertEqual(
        num_subcuentas, int(x),
        f'La página {cuenta} muestra {num_subcuentas} subcuentas, no {x}.'
    )


@then('veo las subcuentas de "{nombre_cta}"')
def detalle_muestra_subcuentas_de(context, nombre_cta):
    cta = Cuenta.tomar(nombre=nombre_cta.lower())
    subctas_pag = [x.text for x in context.browser.esperar_elementos(
        'link_cuenta'
    )]
    context.test.assertEqual(
        subctas_pag,
        [x.nombre for x in cta.subcuentas.all()]
    )


@then('veo el titular de "{nombre_cta}"')
def veo_titular_de(context, nombre_cta):
    cta = Cuenta.tomar(nombre=nombre_cta.lower())
    titular_pag = context.browser.esperar_elemento(
        'class_span_titular', By.CLASS_NAME).text.strip()

    context.test.assertEqual(titular_pag, cta.titular.nombre)


@then('veo los titulares de las subcuentas de "{nombre_cta}"')
def veo_titulares_de(context, nombre_cta):
    cta = Cuenta.tomar(nombre=nombre_cta.lower())
    titulares_pag = [
        x.text.strip() for x in
            context.browser.esperar_elementos('class_span_titular')
    ]
    titulares_cta = [x.nombre for x in cta.titulares]

    context.test.assertEqual(titulares_pag, titulares_cta)


@then('veo que el saldo {tal} es {tantos} pesos')
def el_saldo_tal_es_tanto(context, tal, tantos):
    # TODO: Refactor
    if tal in ('general', 'de la página'):
        total = context.browser.esperar_elemento('id_div_importe_saldo_pag')
    else:
        if tal == 'de la cuenta':
            slug = 'e'
        else:
            tal = tal[3:]
            if tal[0] == '"':
                tal = tal[1:-1]
            slug = Cuenta.tomar(nombre=tal.lower()).slug
        total = context.browser.esperar_elemento(f'id_saldo_cta_{slug}')

    if tantos == 'cero':
        tantos = '0.00'
    elif tantos.find('.') == -1:
        tantos += '.00'

    context.test.assertEqual(
        total.text, tantos
    )


@then('veo que el nombre de la cuenta es "{nombre}"')
def el_nombre_es_tal(context, nombre):
    nombre_en_pag = context.browser.esperar_elemento(
        'class_nombre_cuenta', By.CLASS_NAME).text
    context.test.assertEqual(nombre_en_pag, nombre)


@then('veo sólo los movimientos relacionados con "{nombre_cta}" o con sus subcuentas')
def veo_solo_movimientos_relacionados_con_cta_o_subctas(context, nombre_cta):
    cta = Cuenta.tomar(nombre=nombre_cta.lower())
    movs_pag = [x.text for x in context.browser.esperar_elementos(
        '.class_row_mov td.class_td_concepto',
        By.CSS_SELECTOR
    )]
    context.test.assertEqual(movs_pag, [x.concepto for x in cta.movs()])


@then('veo sólo los movimientos relacionados con "{nombre_cta}"')
def veo_solo_movimientos_relacionados_con(context, nombre_cta):
    context.execute_steps(
        f'Entonces veo sólo los movimientos relacionados con "{nombre_cta}" '
        f'o con sus subcuentas'
    )


@then('veo una cuenta en la grilla con nombre "{nombre}"')
def veo_una_cuenta(context, nombre):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertIn(
        nombre.lower(),
        [x.find_element_by_class_name('class_nombre_cuenta').text
         for x in cuentas]
    )


@then('veo una cuenta en la grilla')
def veo_una_cuenta(context):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertEqual(len(cuentas), 1)


@then('veo un mensaje de saldos erróneos que incluye las cuentas')
def veo_mensaje_de_saldos_erroneos(context):
    msj = context.browser.esperar_elemento('id_msj_ctas_erroneas').text
    for fila in context.table:
        context.test.assertIn(fila['nombre'].lower(), msj)


@then('veo un mensaje de saldo erróneo para la cuenta "{nombre}"')
def veo_mensaje_de_saldo_erroneo(context, nombre):
    context.execute_steps(
        'Entonces veo un mensaje de saldos erróneos que incluye las cuentas\n'
        f'    | nombre |\n| {nombre.lower()} |'
    )


# CONSTATACIONES DE MOVIMIENTO

@then('veo un movimiento con los siguientes valores')
def veo_un_movimiento(context):
    movs_concepto = [
        c.text for c in context.browser.esperar_elementos('class_td_concepto')
    ]
    movs_importe = [
        c.text for c in context.browser.esperar_elementos('class_td_importe')
    ]
    movs_ctas = [
        c.text for c in context.browser.esperar_elementos('class_td_cuentas')
    ]
    for fila in context.table:
        context.test.assertIn(fila['concepto'], movs_concepto)
        indice = movs_concepto.index(fila['concepto'])
        context.test.assertEqual(movs_importe[indice], fila['importe'])
        if fila.get('cta_entrada'):
            context.test.assertIn(
                fila['cta_entrada'].lower(), movs_ctas[indice])
        if fila.get('cta_salida'):
            context.test.assertIn(
                fila['cta_salida'].lower(), movs_ctas[indice])


@then('veo {num} movimient{os} en la página')
def veo_movimiento(context, num, os):
    num = int(CARDINALES.get(num, num))

    lista_ult_movs = context.browser.esperar_elemento('id_lista_ult_movs')
    ult_movs = lista_ult_movs.find_elements_by_tag_name('tr')

    context.test.assertEqual(len(ult_movs), num+1)  # El encabezado y un movimiento


@then('veo {num} "{entidades}" en la página')
def veo_cosas(context, num, entidades):
    num = CARDINALES.get(num, int(num))
    entidades = LISTAS_DE_ENTIDADES['entidades']

    elementos = context.browser.esperar_elementos(entidades)

    context.test.assertEqual(len(elementos), num)


@then('el campo "{campo}" del formulario tiene fecha de hoy '
      'como valor por defecto')
def campo_muestra_fecha_de_hoy(context, campo):
    campo_fecha = context.browser.esperar_elemento(f'id_{campo}')
    context.test.assertEqual(campo_fecha.get_attribute("value"), hoy())


@then('los movimientos en la página tienen estos valores')
def movs_en_pagina_coinciden_con(context):
    conceptos = [e.text for e in
                 context.browser.esperar_elementos('class_td_concepto')]
    importes = [e.text for e in
                context.browser.esperar_elementos('class_td_importe')]
    cuentas = [e.text for e in
               context.browser.esperar_elementos('class_td_cuentas')]

    for i, fila in enumerate(context.table):
        context.test.assertEqual(
            conceptos[i], fila['concepto'],
            f"El concepto {fila['concepto']} no coincide con {conceptos[i]}"
        )
        importe = f"{float(fila['importe']):.2f}"
        context.test.assertEqual(
            importes[i], importe,
            f"El importe del mov {i+1} es {importes[i]}, no {importe}"
        )
        context.test.assertEqual(
            cuentas[i], fila['cuentas'].lower(),
            f"Las cuentas involucradas en el mov {i+1} son {cuentas[i]}, "
            f"no {fila['cuentas']}"
        )


@then('veo que el concepto del movimiento es "{concepto}"')
def el_concepto_es_tal(context, concepto):
    concepto_en_pag = context.browser.esperar_elemento(
        'class_td_concepto', By.CLASS_NAME).text
    context.test.assertEqual(concepto_en_pag, concepto)


@then('veo que el importe del movimiento "{concepto}" es {tantos} pesos')
def el_importe_es_tanto(context, concepto, tantos):

    if tantos.find('.') == -1:
        tantos += '.00'

    movimiento = context.browser.esperar_movimiento(concepto)
    importe = movimiento.find_element_by_class_name('class_td_importe').text

    context.test.assertEqual(importe, tantos)


@then('veo que la cuenta de {sentido} del movimiento "{concepto}" es "{esta}"')
def cuenta_mov_es(context, sentido, concepto, esta):
    movimiento = context.browser.esperar_movimiento(concepto)
    cuentas = movimiento.find_element_by_class_name('class_td_cuentas').text

    if sentido == "entrada":
        signo = '+'
    elif sentido == "salida":
        signo = '-'
    else: raise errors.ErrorOpcionInexistente(
        'Las opciones posibles son "entrada" y "salida".'
    )

    context.test.assertIn(signo+esta.lower(), cuentas)


@then('veo que el movimiento "{concepto}" no tiene cuenta de {sentido}')
def mov_no_tiene_cuenta(context, concepto, sentido):
    movimiento = context.browser.esperar_movimiento(concepto)
    cuentas = movimiento.find_element_by_class_name('class_td_cuentas').text

    if sentido == "entrada":
        signo = '+'
    elif sentido == "salida":
        signo = '-'
    else: raise errors.ErrorOpcionInexistente(
        'Las opciones posibles son "entrada" y "salida".'
    )

    context.test.assertNotIn(signo, cuentas)


@then('veo que "{nombre}" no está entre las cuentas del movimiento "{concepto}"')
def cuenta_no_esta_en_mov(context, nombre, concepto):
    movimiento = context.browser.esperar_movimiento(concepto)
    cuentas = movimiento.find_element_by_class_name('class_td_cuentas').text

    context.test.assertNotIn(nombre, cuentas)
