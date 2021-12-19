from diario.models import Titular
from fts.driver import FinperFirefox


def before_all(context):
    context.browser = FinperFirefox()

    # TODO: ¿Por qué tengo que hacer esto? ¿Por qué me aparece un titular por
    #       defecto si yo no creé ninguno? Averiguar:
    #       Tiene que ver con que se usa como default de
    #       'CuentaInteractiva.Titular' el classmethod 'Titular.por_defecto'
    #       Aparentemente, se estaría llamando a esa función y generando un
    #       titular antes de before_all.
    #       Mientras no lo resolvamos, habrá que limpiar la base de datos
    #       antes de los tests.
    #       Lo más probable es que en algún momento retire por completo el
    #       método 'Titular.por_defecto' como default de
    #       'CuentaInteractiva.Titular', con lo cual podré retirar también
    #       esto y aquí no ha pasado nada.
    Titular.todes().delete()


def after_all(context):
    context.browser.quit()


def before_feature(context, feature):
    if 'skip' in feature.tags:
        feature.skip('Característica marcada con @skip')
        return


def before_scenario(context, scenario):
    if 'skip' in scenario.effective_tags:
        scenario.skip('Escenario marcado con skip')
        return
