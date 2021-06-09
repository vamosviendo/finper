from fts.base import MiFirefox, FunctionalTest


def before_all(context):
    context.browser = MiFirefox()
    context.ft = FunctionalTest()


def after_all(context):
    context.browser.quit()


def before_feature(context, feature):
    pass