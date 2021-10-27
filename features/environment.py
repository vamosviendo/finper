from diario.models import Titular
from fts.driver import FinperFirefox


def before_all(context):
    context.browser = FinperFirefox()


def after_all(context):
    context.browser.quit()


def before_feature(context, feature):
    pass


def before_scenario(context, scenario):
    if "sec" in scenario.feature.tags:
        Titular.crear(titname='titular')