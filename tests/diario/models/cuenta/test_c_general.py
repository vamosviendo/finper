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
    primera_cuenta.sk = 'PC'
    primera_cuenta.clean_save()

    segunda_cuenta = Cuenta()
    segunda_cuenta.nombre = 'Segunda cuenta'
    segunda_cuenta.sk = 'SC'
    segunda_cuenta.clean_save()

    cuentas_guardadas = Cuenta.todes()
    assert cuentas_guardadas.count() == 2

    primera_cuenta_guardada = primera_cuenta.tomar_de_bd()
    segunda_cuenta_guardada = segunda_cuenta.tomar_de_bd()

    assert primera_cuenta_guardada.nombre == 'primera cuenta'
    assert primera_cuenta_guardada.sk == 'pc'
    assert segunda_cuenta_guardada.nombre == 'segunda cuenta'
    assert segunda_cuenta_guardada.sk == 'sc'


def test_guarda_fecha_de_creacion(fecha):
    cuenta = Cuenta(nombre='Cuenta', sk='C', fecha_creacion=fecha)
    cuenta.clean_save()
    assert cuenta.fecha_creacion == fecha


def test_guarda_fecha_actual_por_defecto():
    cuenta = Cuenta(nombre='Cuenta', sk='C')
    cuenta.clean_save()
    assert cuenta.fecha_creacion == date.today()


def test_cuenta_creada_tiene_saldo_cero_por_defecto():
    cuenta = Cuenta(nombre='Cuenta', sk='C')
    cuenta.clean_save()
    assert cuenta.saldo() == 0


def test_sk_no_permite_caracteres_no_alfanumericos():
    with pytest.raises(ValidationError):
        Cuenta.crear(nombre='Efectivo', sk='E!ec')


def test_cuentas_se_ordenan_por_nombre(titular_principal):
    cuenta1 = Cuenta.crear(nombre='Efectivo', sk='E')
    cuenta2 = Cuenta.crear(nombre='Banco', sk='ZZ')
    cuenta3 = Cuenta.crear(nombre='Cuenta Corriente', sk='CC')

    assert list(Cuenta.todes()) == [cuenta2, cuenta3, cuenta1]


def test_cuenta_se_relaciona_con_una_moneda(peso, dolar):
    cuenta = Cuenta(nombre='Cuenta en pesos', sk='c', moneda=peso)
    cuenta.clean_save()
    cuenta_recuperada = Cuenta.tomar(sk='c')
    assert cuenta_recuperada.moneda == peso
    cuenta_en_us = Cuenta(nombre='Cuenta en dolares', sk='d', moneda=dolar)
    cuenta_en_us.clean_save()
    cuenta_recuperada = Cuenta.tomar(sk='d')
    assert cuenta_recuperada.moneda == dolar


def test_toma_moneda_base_como_moneda_por_defecto(peso):
    cuenta = Cuenta(nombre='Cuenta', sk='c')
    cuenta.clean_save()
    cuenta_recuperada = Cuenta.tomar(sk='c')
    assert cuenta_recuperada.moneda == peso


def test_natural_key_devuelve_id_basada_en_sk(cuenta):
    assert cuenta.natural_key() == (cuenta.sk, )
