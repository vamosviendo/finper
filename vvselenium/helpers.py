import time

from selenium.common.exceptions import WebDriverException

from django.contrib.auth import get_user_model


User = get_user_model()


def esperar(condicion, tiempo=2):
    """ Devuelve una función que espera un tiempo
        que se cumpla una condición.
        Requiere: time
                  selenium.common.exceptions.WebDriverException
    """

    def condicion_modificada(*args, **kwargs):
        arranque = time.time()
        while True:
            try:
                return condicion(*args, **kwargs)
            except (AssertionError, WebDriverException) as noesperomas:
                if time.time() - arranque > tiempo:
                    raise noesperomas
                time.sleep(0.2)

    return condicion_modificada


def table_to_str(tabla):
    """
    Convierte un context.table en un str apto para ser pasado en
    context.execute_steps()
    :param tabla: Un objeto context.table
    :return: un str con formato de tabla con celdas divididas por |
    """
    result = ''
    if tabla.headings:
        result = '|'
    for enc in tabla.headings:
        result += enc + '|'
    result += '\n'
    for fila in tabla.rows:
        if fila.cells:
            result += '|'
        for cell in fila.cells:
            result += cell + '|'
        result += '\n'
    return result


def espacios_a_camelcase(cadena):
    lista = cadena.split(' ')
    return ''.join(lista[0:1] + [x.capitalize() for x in lista[1:]])


def espacios_a_snake(cadena):
    return '_'.join(cadena.split(' '))


def tomar_atributo(objeto, atributo):
    return getattr(objeto, espacios_a_snake(atributo))


def fijar_atributo(objeto, atributo, valor):
    setattr(objeto, espacios_a_snake(atributo), valor)


@esperar
def espera(funcion):
    """ Espera el tiempo por default y ejecuta función."""
    return funcion()


def crear_usuario_base(username, password):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username=username, password=password)
    return user.username


def overrides(step_text, step_keyword='step'):
    """ Decorator. Hace que un step sobrescriba otro del mismo nombre, siempre
        y cuando el otro esté en un archivo que se lee antes que el de él
        (anterior alfabéticamente).
        Tomado de acá: https://github.com/behave/behave/issues/853 """
    from behave.runner import the_step_registry
    step_type = step_keyword.lower()
    assert step_type in ('given', 'when', 'then', 'step'), f'Invalid step type: {step_type}'
    step_definitions = the_step_registry.steps[step_type]

    def step_decorator(func):
        deco = the_step_registry.make_decorator(step_type)
        for index, existing in enumerate(step_definitions):
            if existing.match(step_text):
                break
        else:
            print('no existing definition to override!')
            deco = deco(step_text)
            return deco(func)

        print(f'replacing step {existing.describe()} from {existing.location} with {func}')
        step_definitions.pop(index)
        deco = deco(step_text)
        return deco(func)  # apply the decorator normally

    return step_decorator


def if_not_defined(step_text, step_keyword='step'):
    """ Decorator. Hace que el step se ejecute solamente si no hay definido
        un step del mismo nombre en otro sitio.
        Tomado de acá: https://github.com/behave/behave/issues/853 """
    from behave.runner import the_step_registry
    step_type = step_keyword.lower()
    assert step_type in ('given', 'when', 'then', 'step'), f'Invalid step type: {step_type}'
    step_definitions = the_step_registry.steps[step_type]

    def step_decorator(func):
        deco = the_step_registry.make_decorator(step_type)
        for index, existing in enumerate(step_definitions):
            if existing.match(step_text):
                break
        else:
            print(f'{step_text} not yet defined! Adding now!')
            deco = deco(step_text)
            return deco(func)

        print(f'step {existing.describe()} already exists in {existing.location}, doing nothing!')
        return func
    return step_decorator
