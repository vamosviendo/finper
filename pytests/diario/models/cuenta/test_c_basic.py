from datetime import date

import pytest

from django.core.exceptions import ValidationError

from diario.models import Cuenta


@pytest.fixture(autouse=True)
def tit(titular):
    return titular


def test_guarda_y_recupera_cuentas():
    primera_cuenta = Cuenta()
    primera_cuenta.nombre = 'Primera cuenta'
    primera_cuenta.slug = 'PC'
    primera_cuenta.full_clean()
    primera_cuenta.save()

    segunda_cuenta = Cuenta()
    segunda_cuenta.nombre = 'Segunda cuenta'
    segunda_cuenta.slug = 'SC'
    segunda_cuenta.full_clean()
    segunda_cuenta.save()

    cuentas_guardadas = Cuenta.todes()
    assert cuentas_guardadas.count() == 2

    primera_cuenta_guardada = primera_cuenta.tomar_de_bd()
    segunda_cuenta_guardada = segunda_cuenta.tomar_de_bd()

    assert primera_cuenta_guardada.nombre == 'primera cuenta'
    assert primera_cuenta_guardada.slug == 'pc'
    assert segunda_cuenta_guardada.nombre == 'segunda cuenta'
    assert segunda_cuenta_guardada.slug == 'sc'


def test_guarda_fecha_de_creacion(fecha):
    cuenta = Cuenta(nombre='Cuenta', slug='C', fecha_creacion=fecha)
    cuenta.full_clean()
    cuenta.save()
    assert cuenta.fecha_creacion == fecha


def test_guarda_fecha_actual_por_defecto():
    cuenta = Cuenta(nombre='Cuenta', slug='C')
    cuenta.full_clean()
    cuenta.save()
    assert cuenta.fecha_creacion == date.today()


def test_cuenta_creada_tiene_saldo_cero_por_defecto():
    cuenta = Cuenta(nombre='Cuenta', slug='C')
    cuenta.save()
    assert cuenta.saldo == 0


def test_slug_no_permite_caracteres_no_alfanumericos():
    with pytest.raises(ValidationError):
        Cuenta.crear(nombre='Efectivo', slug='E!ec')


def test_cuentas_se_ordenan_por_nombre():
    cuenta1 = Cuenta.crear(nombre='Efectivo', slug='E')
    cuenta2 = Cuenta.crear(nombre='Banco', slug='ZZ')
    cuenta3 = Cuenta.crear(nombre='Cuenta Corriente', slug='CC')

    assert list(Cuenta.todes()) == [cuenta2, cuenta3, cuenta1]
