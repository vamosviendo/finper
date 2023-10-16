from datetime import date

from diario.models import Titular, CuentaInteractiva


def test_guarda_y_recupera_titulares(fecha):
    titular = Titular()
    titular.titname = "juan"
    titular.nombre = 'Juan Juánez'
    titular.fecha_alta = fecha
    titular.full_clean()
    titular.save()

    assert Titular.cantidad() == 1
    tit = Titular.tomar(titname="juan")
    assert tit.nombre == "Juan Juánez"
    assert tit.fecha_alta == fecha


def test_si_no_se_proporciona_nombre_toma_titname_como_nombre():
    titular = Titular(titname='juan')
    titular.full_clean()

    titular.save()
    tit = Titular.tomar(titname='juan')

    assert tit.nombre == 'juan'


def test_toma_fecha_actual_como_fecha_de_alta_por_defecto():
    titular = Titular(titname='juan')
    titular.full_clean()
    titular.save()

    tit = Titular.tomar(titname='juan')
    assert tit.fecha_alta == date.today()


def test_se_relaciona_con_cuentas(titular):
    cuenta = CuentaInteractiva(nombre='cuenta', slug='cta')
    cuenta.titular = titular
    cuenta.full_clean()
    cuenta.save()

    assert cuenta in titular.cuentas.all()


def test_str_devuelve_nombre_titular(titular):
    assert str(titular) == titular.nombre
