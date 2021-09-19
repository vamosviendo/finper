from steps.helpers import FinperFirefox


def before_all(context):
    context.browser = FinperFirefox()


def after_all(context):
    context.browser.quit()


def before_feature(context, feature):
    pass