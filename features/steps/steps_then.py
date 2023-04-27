""" Las implementaciones deben ir de lo más particular a lo más general.
    Por ejemplo:
        @when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
        @when('agrego una cuenta con nombre "{nombre}"')
        @when('agrego una cuenta')
"""
from behave import then
from selenium.webdriver.common.by import By

from consts import LISTAS_DE_ENTIDADES
from features.helpers import formatear_importe
from vvsteps.consts import CARDINALES
from diario.models import Cuenta, Titular
from utils import errors
from utils.tiempo import hoy
from utils.numeros import float_format
from utils.texto import truncar
from vvsteps.helpers import table_to_str, fijar_atributo
""" Steps en el archivo:
@then('el saldo general es {tantos} pesos')
@then('la cuenta "{slug}" tiene saldo {monto}')
@then('las subcuentas de la página de {cuenta} tienen estos valores')
@then('veo {x} subcuentas en la página {cuenta}')
@then('veo las subcuentas de "{nombre_cta}"')
@then('veo el titular de "{nombre_cta}"')
@then('veo que el titular de la cuenta es "{nombre_titular}"')
@then('veo los titulares de las subcuentas de "{nombre_cta}"')
@then('veo que el saldo {tal} es {tantos} pesos')
@then('veo que el nombre de la cuenta es "{nombre}"')

@then('la lista de movimientos está vacia')
@then('veo la siguiente lista de movimientos')
@then('veo sólo los movimientos relacionados con "{nombre_cta}" o con sus subcuentas')
@then('veo sólo los movimientos relacionados con "{nombre_cta}"')
@then('veo sólo los movimientos relacionados con cuentas de "{nombre_titular}"')
@then('veo que los movimientos en la página son los siguientes')
@then('veo entre los movimientos de la página los siguientes')
@then('no veo movimientos con concepto "{concepto}"')
@then('veo un movimiento con concepto "{concepto}"')
@then('veo un movimiento con los siguientes valores')
@then('veo {num} movimient{os} en la página')
@then('veo que el concepto del movimiento es "{concepto}"')
@then('veo que el importe del movimiento "{concepto}" es {tantos} pesos')
@then('veo que la cuenta de {sentido} del movimiento "{concepto}" es "{esta}"')
@then('veo que la fecha del movimiento de detalle "{detalle}" es "{esta}"')
@then('veo que el movimiento "{concepto}" no tiene cuenta de {sentido}')
@then('veo que "{nombre}" no está entre las cuentas del movimiento "{concepto}"')

@then('la grilla de cuentas está vacia')
@then('veo una cuenta en la grilla con slug "{slug}" y nombre "{nombre}"')
@then('veo una cuenta en la grilla con nombre "{nombre}"')
@then('no veo una cuenta con nombre {nombre} en la grilla')
@then('veo una cuenta en la grilla con slug "{slug}"')
@then('no veo una cuenta con slug "{slug}" en la grilla')
@then('veo una cuenta en la grilla')

@then('veo un titular en la grilla con nombre "{nombre}"')
@then('veo un titular en la grilla')
@then('no veo un titular con nombre "{nombre}" en la grilla')
@then('veo que el capital de "{titular}" es {tantos} pesos')

@then('veo un mensaje de saldos erróneos que incluye las cuentas')
@then('veo un mensaje de saldo erróneo para la cuenta "{nombre}"')
@then('soy dirigido a la página "{pag}" de la cuenta "{nombre}"')
@then('soy dirigido a la página "{pag}" del titular "{nombre}"')
@then('veo {num} "{entidades}" en la página')
@then('el campo "{campo}" del formulario tiene fecha de hoy como valor por defecto'
"""


# CONSTATACIONES GENERALES

@then('el saldo general es {tantos} pesos')
def saldo_general_es(context, tantos):
    context.test.assertEqual(
        context.browser.esperar_elemento('id_div_importe_saldo_pag').text,
        tantos
    )


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
    titulos = [e.get_attribute("title") for e in
               context.browser.esperar_elementos('class_link_cuenta')]
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
            nombres[i], fila['slug'].upper(),
            f"El slug {fila['slug']} no coincide con {nombres[i]}."
        )
        context.test.assertEqual(
            titulos[i], fila['nombre'].lower(),
            f"El nombre {fila['nombre']} no coincide con {titulos[i]}."
        )
        saldo = float_format(fila['saldo'])
        context.test.assertEqual(
            saldos[i], saldo,
            f"El saldo de {fila['nombre']} es {saldos[i]}, no {saldo}."
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
        'class_link_cuenta'
    )]
    context.test.assertEqual(
        subctas_pag,
        [x.slug.upper() for x in cta.subcuentas.all()]
    )


@then('veo el titular de "{nombre_cta}"')
def veo_titular_de(context, nombre_cta):
    cta = Cuenta.tomar(nombre=nombre_cta.lower())
    context.execute_steps(
        f'Entonces veo que el titular de la cuenta es "{cta.titular.nombre}"')


@then('veo que el titular de la cuenta es "{nombre_titular}"')
def veo_que_titular_es(context, nombre_titular):
    titular_pag = context.browser.esperar_elemento(
        'class_div_nombre_titular', By.CLASS_NAME).text.strip()
    context.test.assertEqual(titular_pag, nombre_titular)


@then('veo los titulares de las subcuentas de "{nombre_cta}"')
def veo_titulares_de(context, nombre_cta):
    cta = Cuenta.tomar(nombre=nombre_cta.lower())
    titulares_pag = [
        x.text.strip() for x in
            context.browser.esperar_elementos('class_div_nombre_titular')
    ]
    titulares_cta = [x.nombre for x in cta.titulares]

    context.test.assertEqual(titulares_pag, titulares_cta)


@then('veo que el saldo {tal} es {tantos} pesos')
def el_saldo_tal_es_tanto(context, tal, tantos):
    if tal in ('general', 'de la página'):
        total = context.browser.esperar_elemento(
            'id_div_importe_saldo_pag').text
    else:
        if tal == 'de la cuenta':
            slug = 'e'
        else:
            tal = tal[3:]
            if tal[0] == '"':
                tal = tal[1:-1]
            slug = Cuenta.tomar(nombre=tal.lower()).slug
        total = context.browser.esperar_elemento(f'id_saldo_cta_{slug}').text

    tantos = formatear_importe(tantos)

    context.test.assertEqual(total, tantos)


@then('veo que el nombre de la cuenta es "{nombre}"')
def el_nombre_es_tal(context, nombre):
    nombre_en_pag = context.browser.esperar_elemento(
        'class_link_cuenta', By.CLASS_NAME).get_attribute('title')
    context.test.assertEqual(nombre_en_pag, nombre)


@then('la lista de movimientos está vacia')
def lista_movimientos_vacia(context):
    movs = context.browser.esperar_elementos('tr', By.TAG_NAME)
    context.test.assertEqual(len(movs), 1)


@then('veo la siguiente lista de movimientos')
def veo_lista_de_movimientos(context):
    movs_pag = context.browser.esperar_elementos('class_row_mov')

    for i, fila in enumerate(context.table):
        for k in fila.headings:
            context.test.assertEqual(
                movs_pag[i].esperar_elemento(f'class_td_{k}', By.CLASS_NAME).text,
                fila[k],
            )


@then('veo movimientos con los siguientes valores')
def veo_valores_de_movimientos(context):
    context.execute_steps(
        f'entonces veo la siguiente lista de movimientos:\n {table_to_str(context.table)}'
    )


@then('veo sólo los movimientos relacionados con "{nombre_cta}" o con sus subcuentas')
def veo_solo_movimientos_relacionados_con_cta_o_subctas(context, nombre_cta):
    cta = Cuenta.tomar(nombre=nombre_cta.lower())
    movs_pag = [x.text for x in context.browser.esperar_elementos(
        '.class_row_mov td.class_td_concepto',
        By.CSS_SELECTOR
    )]
    context.test.assertEqual(
        movs_pag,
        list(reversed([x.concepto for x in cta.movs()]))
    )


@then('veo sólo los movimientos relacionados con "{nombre_cta}"')
def veo_solo_movimientos_relacionados_con(context, nombre_cta):
    context.execute_steps(
        f'Entonces veo sólo los movimientos relacionados con "{nombre_cta}" '
        f'o con sus subcuentas'
    )


@then('veo sólo los movimientos relacionados con cuentas de "{nombre_titular}"')
def veo_solo_movimientos_relacionados_con(context, nombre_titular):
    titular = Titular.tomar(nombre=nombre_titular)
    movs_pag = [x.text for x in context.browser.esperar_elementos(
        '.class_row_mov td.class_td_concepto',
        By.CSS_SELECTOR
    )]
    context.test.assertEqual(
        movs_pag,
        [x.concepto for x in titular.movimientos()]
    )


@then('veo que los movimientos en la página son los siguientes')
def movs_en_pagina_coinciden_con(context):

    for i, fila in enumerate(context.table):
        for heading in fila.headings:
            td = [
                e.text for e in
                context.browser.esperar_elementos(f'class_td_{heading}')
            ][i]
            if heading == 'detalle':
                context.test.assertEqual(td, truncar(fila[heading], 50))
            else:
                context.test.assertEqual(td, fila[heading])


@then('veo entre los movimientos de la página los siguientes')
def veo_movimientos(context):

    # Tomar filas y columnas de la página
    filas = context.browser.esperar_elementos('class_row_mov')
    columnas = dict()
    for heading in context.table.headings:
        columnas[heading] = [
            c.find_element_by_class_name(f'class_td_{heading}').text
            for c in filas
        ]

    # Buscar en ellas filas y columnas de context.table
    for i, fila in enumerate(context.table):
        primera_columna = list(columnas.keys())[0]
        context.test.assertIn(
            fila[primera_columna],
            columnas[primera_columna],
            f'El movimiento de {primera_columna} "{fila[primera_columna]}" '
            f'no se encuentra en la página'
        )
        indice = columnas[primera_columna].index(fila[primera_columna])

        otras_columnas = columnas.copy()
        otras_columnas.pop(primera_columna)

        for columna in otras_columnas:
            context.test.assertEqual(
                otras_columnas[columna][indice],
                fila[columna],
                f'El campo {columna} del movimiento '
                f'de {primera_columna} "{fila[primera_columna]}" '
                f'no es {fila[columna]} sino {otras_columnas[columna][indice]}'
            )

    fijar_atributo(context, "movimientos", filas)


@then('no veo movimientos con concepto "{concepto}"')
def no_veo_movimientos(context, concepto):
    movs_concepto = [
        c.text for c in context.browser.esperar_elementos('class_td_concepto')
    ]
    context.test.assertNotIn(concepto, movs_concepto)


@then('veo un movimiento con concepto "{concepto}"')
def veo_movimientos(context, concepto):
    movs_concepto = [
        c.text for c in context.browser.esperar_elementos('class_td_concepto')
    ]
    context.test.assertIn(concepto, movs_concepto)


@then('veo un movimiento con los siguientes valores')
def veo_un_movimiento(context):
    context.execute_steps(f'''
        Entonces veo entre los movimientos de la página los siguientes
        {table_to_str(context.table)}
    ''')


@then('veo {num} movimient{os} en la página')
def veo_movimiento(context, num, os):
    num = int(CARDINALES.get(num, num))

    lista_ult_movs = context.browser.esperar_elemento('id_lista_ult_movs')
    ult_movs = lista_ult_movs.find_elements_by_tag_name('tr')

    context.test.assertEqual(len(ult_movs), num+1)  # El encabezado y un movimiento


@then('veo que el concepto del movimiento es "{concepto}"')
def el_concepto_es_tal(context, concepto):
    concepto_en_pag = context.browser.esperar_elemento(
        'class_td_concepto', By.CLASS_NAME).text
    context.test.assertEqual(concepto_en_pag, concepto)


@then('veo que el importe del movimiento "{concepto}" es {tantos} pesos')
def el_importe_es_tanto(context, concepto, tantos):

    if tantos.find('.') == -1:
        tantos += ',00'

    movimiento = context.browser.esperar_movimiento("concepto", concepto)
    importe = movimiento.find_element_by_class_name('class_td_importe').text

    context.test.assertEqual(importe, tantos)


@then('veo que la cuenta de {sentido} del movimiento "{concepto}" es "{esta}"')
def cuenta_mov_es(context, sentido, concepto, esta):
    movimiento = context.browser.esperar_movimiento("concepto", concepto)
    cuentas = movimiento.find_element_by_class_name('class_td_cuentas').text

    if sentido == "entrada":
        signo = '+'
    elif sentido == "salida":
        signo = '-'
    else: raise errors.ErrorOpcionInexistente(
        'Las opciones posibles son "entrada" y "salida".'
    )
    slug = Cuenta.tomar(nombre=esta.lower()).slug

    context.test.assertIn(signo+slug, cuentas)


@then('veo que la fecha del movimiento de detalle "{detalle}" es "{esta}"')
def fecha_mov_es(context, detalle, esta):
    movimiento = context.browser.esperar_movimiento('detalle', detalle)
    fecha = movimiento.find_element_by_class_name('class_td_fecha').text

    context.test.assertEqual(fecha, esta)


@then('veo que el movimiento "{concepto}" no tiene cuenta de {sentido}')
def mov_no_tiene_cuenta(context, concepto, sentido):
    movimiento = context.browser.esperar_movimiento("concepto", concepto)
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
    movimiento = context.browser.esperar_movimiento("concepto", concepto)
    cuentas = movimiento.find_element_by_class_name('class_td_cuentas').text

    context.test.assertNotIn(nombre, cuentas)


@then('la grilla de cuentas está vacia')
def grilla_cuentas_vacia(context):
    cuentas = context.browser.esperar_elementos('class_div_cuenta', fail=False)
    context.test.assertEqual(len(cuentas), 0)


@then('veo una cuenta en la grilla con slug "{slug}" y nombre "{nombre}"')
def veo_una_cuenta(context, slug, nombre):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    div_cuenta = next(x
                      for x in cuentas
                      if x.get_attribute('id') == f'id_div_cta_{slug.lower()}')
    slug_cuenta = div_cuenta.find_element_by_class_name(
        'class_nombre_cuenta').text
    nombre_cuenta = div_cuenta.find_element_by_class_name(
        'class_link_cuenta').get_attribute('title')
    context.test.assertEqual(slug_cuenta, slug.upper())
    context.test.assertEqual(nombre_cuenta, nombre.lower())


@then('veo una cuenta en la grilla con nombre "{nombre}"')
def veo_una_cuenta(context, nombre):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertIn(
        nombre.lower(),
        [x.find_element_by_class_name('class_link_cuenta')
             .get_attribute('title') for x in cuentas]
    )


@then('no veo una cuenta con nombre "{nombre}" en la grilla')
def cuenta_no_esta_en_grilla(context, nombre):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertNotIn(
        nombre.lower(),
        [x.find_element_by_class_name('class_link_cuenta')
             .get_attribute('title') for x in cuentas]
    )


@then('veo una cuenta en la grilla con slug "{slug}"')
def veo_una_cuenta(context, slug):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertIn(
        slug.upper(),
        [x.find_element_by_class_name('class_nombre_cuenta').text
         for x in cuentas]
    )


@then('no veo una cuenta con slug "{slug}" en la grilla')
def cuenta_no_esta_en_grilla(context, slug):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertNotIn(
        slug.upper(),
        [x.find_element_by_class_name('class_nombre_cuenta').text
         for x in cuentas]
    )


@then('veo una cuenta en la grilla')
def veo_una_cuenta(context):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertEqual(len(cuentas), 1)


@then('veo un titular en la grilla con nombre "{nombre}"')
def veo_una_cuenta(context, nombre):
    titulares = context.browser.esperar_elementos('class_div_titular')
    context.test.assertIn(
        nombre,
        [x.find_element_by_class_name('class_link_titular').text
            for x in titulares]
    )


@then('veo un titular en la grilla')
def veo_un_titular(context):
    titulares = context.browser.esperar_elementos('class_div_titular')
    context.test.assertEqual(len(titulares), 1)


@then('no veo un titular con nombre "{nombre}" en la grilla')
def titular_no_esta_en_grilla(context, nombre):
    titulares = context.browser.esperar_elementos('class_div_titular')
    context.test.assertNotIn(
        nombre,
        [x.find_element_by_class_name('class_link_titular').text
         for x in titulares]
    )


@then('veo que el capital de "{titular}" es {tantos} pesos')
def el_capital_es_tanto(context, titular, tantos):
    titname = Titular.tomar(nombre=titular).titname

    tantos = formatear_importe(tantos)

    patri = context.browser.esperar_elemento(f'id_capital_{titname}')
    context.test.assertEqual(patri.text, tantos)


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


@then('soy dirigido a la página "{pag}" de la cuenta "{nombre}"')
def soy_dirigido_a_pagina_de_cuenta(context, pag, nombre):
    cuenta = Cuenta.tomar(nombre=nombre).slug
    context.execute_steps(
        f'Entonces soy dirigido a la página "{pag}" '
        f'con el argumento "{cuenta}"'
    )


@then('soy dirigido a la página "{pag}" del titular "{nombre}"')
def soy_dirigido_a_pagina_de_titular(context, pag, nombre):
    titular = Titular.tomar(nombre=nombre).titname
    context.execute_steps(
        f'Entonces soy dirigido a la página "{pag}" '
        f'con el argumento "{titular}"'
    )


@then('veo {num} "{entidades}" en la página')
def veo_cosas(context, num, entidades):
    num = CARDINALES.get(num, int(num))
    entidades = LISTAS_DE_ENTIDADES['entidades']

    elementos = context.browser.esperar_elementos(entidades)

    context.test.assertEqual(len(elementos), num)


@then('el campo "{campo}" del formulario tiene fecha de hoy como valor por defecto')
def campo_muestra_fecha_de_hoy(context, campo):
    campo_fecha = context.browser.esperar_elemento(f'id_{campo}')
    context.test.assertEqual(campo_fecha.get_attribute("value"), hoy())
