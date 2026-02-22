from datetime import date

from diario.models import Titular, CuentaInteractiva


def test_guarda_y_recupera_titulares(fecha):
    titular = Titular()
    titular.sk = "juan"
    titular.nombre = 'Juan Juánez'
    titular.fecha_alta = fecha
    titular.clean_save()

    assert Titular.cantidad() == 1
    tit = Titular.tomar(sk="juan")
    assert tit.nombre == "Juan Juánez"
    assert tit.fecha_alta == fecha


def test_si_no_se_proporciona_nombre_toma_sk_como_nombre():
    titular = Titular(sk='juan')
    titular.clean_save()
    tit = Titular.tomar(sk='juan')

    assert tit.nombre == 'juan'


def test_toma_fecha_actual_como_fecha_de_alta_por_defecto():
    titular = Titular(sk='juan')
    titular.clean_save()

    tit = Titular.tomar(sk='juan')
    assert tit.fecha_alta == date.today()


def test_se_relaciona_con_cuentas(titular):
    cuenta = CuentaInteractiva(nombre='cuenta', sk='cta')
    cuenta.titular = titular
    cuenta.clean_save()

    assert cuenta in titular.cuentas.all()


def test_str_devuelve_nombre_titular(titular):
    assert str(titular) == titular.nombre


def test_natural_key_devuelve_id_basada_en_sk(titular):
    assert titular.natural_key() == (titular.sk, )
