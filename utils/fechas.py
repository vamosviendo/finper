from datetime import date


def hoy():
    return date.today().strftime('%Y-%m-%d')
