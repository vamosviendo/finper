from behave import given
from selenium.common.exceptions import NoSuchElementException
""" Steps en el archivo:
@given('un "{tag}" de {tipo} "{nombre}"')
@given('un link de texto "{texto}"')
@given('un elemento de {atributo} "{nombre}"')
@given('un usuario identificado')
@given('un usuario no identificado')
"""


@given('un "{tag}" de {tipo} "{nombre}"')
def hay_un_elemento(context, tag, tipo, nombre):
    context.execute_steps(
        f'Entonces veo un "{tag}" de {tipo} "{nombre}"')


@given('un link de texto "{texto}"')
def hay_un_enlace(context, texto):
    context.execute_steps(
        f'Entonces veo un link de texto "{texto}"'
    )


@given('un elemento de {atributo} "{nombre}"')
def hay_un_elemento(context, atributo, nombre):
    """ Busca un elemento con {atributo} {nombre} y lo guarda en el context
        como context.{elemento}
        Ejemplo: Dado un div de id "caja"
                    busca un elemento de id "id_div_caja"
                 Dado un img de clase "miniatura"
                    busca un elemento de clase "class_div_miniatura"
        """
    context.execute_steps(
        f'Entonces veo un elemento de {atributo} "{nombre}"')


@given('un usuario identificado')
def usuario_esta_identificado(context):
    """ Ingresa con nombre de usuario y password"""
    context.execute_steps('''
        Cuando voy a la página "login"
        Y completo y envío el formulario de login
    ''')


@given('un usuario no identificado')
def usuario_no_esta_identificado(context):
    context.execute_steps('cuando voy a la página principal')
    try:
        context.browser.egresar()
    except NoSuchElementException:
        pass
