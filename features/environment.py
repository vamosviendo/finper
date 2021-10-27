from diario.models import Titular
from fts.driver import FinperFirefox


def before_all(context):
    context.browser = FinperFirefox()

    # TODO: ¿Por qué tengo que hacer esto? ¿Por qué me aparece un titular por
    #       defecto si yo no creé ninguno? Averiguar:
    #       Tiene que ver con que se usa como default de
    #       CuentaInteractiva.Titular el classmethod Titular.por_defecto
    #       Aparentemente, se estaría llamando a esa función y generando un
    #       titular antes de before_all.
    #       Mientras no lo resolvamos, habrá que limpiar la base de datos
    #       antes de los tests.
    Titular.todes().delete()


def after_all(context):
    context.browser.quit()


def before_feature(context, feature):
    pass


def before_scenario(context, scenario):

    if not ("no_default_tit" in scenario.tags or
            "no_default_tit" in scenario.feature.tags):
        Titular.crear(titname='tito', nombre='Tito Gómez')