import vvsteps.environment_base as ev
from diario.models import Titular
from fts.base import FinperFirefox


def before_all(context):
    context.browser = FinperFirefox()

    # TODO: ¿Por qué tengo que hacer esto? ¿Por qué me aparece un titular por
    #       defecto si yo no creé ninguno?
    #       Tiene que ver con que se usa como default de
    #       'CuentaInteractiva.Titular' el classmethod 'Titular.por_defecto'
    #       Aparentemente, se estaría llamando a esa función y generando un
    #       titular antes de before_all.
    #       Mientras no lo resolvamos, habrá que limpiar la base de datos
    #       antes de los diario.
    Titular.todes().delete()


def after_all(context):
    ev.after_all(context)


def before_feature(context, feature):
    if 'skip' in feature.tags:
        feature.skip('Característica marcada con @skip')
        return


def before_scenario(context, scenario):
    if 'skip' in scenario.effective_tags:
        scenario.skip('Escenario marcado con skip')
        return
