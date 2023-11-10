from datetime import date

import pytest

from diario.models import Cuenta


@pytest.fixture
def subcuenta_agregada(cuenta_acumulativa, titular):
    return cuenta_acumulativa.agregar_subcuenta('subc3', 'sc3', titular)


def test_crea_nueva_subcuenta(cuenta_acumulativa, titular):
    cant_subcuentas = cuenta_acumulativa.subcuentas.count()
    cuenta_acumulativa.agregar_subcuenta('subc3', 'sc3', titular)
    assert cuenta_acumulativa.subcuentas.count() == cant_subcuentas + 1


def test_devuelve_subcuenta_agregada(cuenta_acumulativa, titular):
    subcuenta_agregada = cuenta_acumulativa.agregar_subcuenta(
        'subc3', 'sc3', titular)
    subcuenta = Cuenta.tomar(slug='sc3')
    assert subcuenta_agregada == subcuenta


def test_subcuenta_agregadada_tiene_saldo_cero(subcuenta_agregada):
    assert subcuenta_agregada.saldo == 0


def test_permite_asignar_titular_distinto_del_de_cuenta_madre(cuenta_acumulativa, otro_titular):
    subcuenta = cuenta_acumulativa.agregar_subcuenta('subc3', 'sc3', titular=otro_titular)
    assert subcuenta.titular == otro_titular


def test_permite_asignar_fecha_de_creacion_a_subcuenta_agregada(
        cuenta_acumulativa, titular, fecha_posterior):
    subcuenta = cuenta_acumulativa.agregar_subcuenta(
        'subc3', 'sc3', titular=titular, fecha=fecha_posterior)
    assert subcuenta.fecha_creacion == fecha_posterior


def test_toma_fecha_actual_por_defecto(cuenta_acumulativa, titular):
    subcuenta = cuenta_acumulativa.agregar_subcuenta('subc3', 'sc3', titular=titular)
    assert subcuenta.fecha_creacion == date.today()


def test_subcuenta_agregada_toma_moneda_de_cuenta_madre(cuenta_acumulativa_en_dolares, titular, dolar):
    subcuenta = cuenta_acumulativa_en_dolares.agregar_subcuenta('subc3', 'sc3', titular=titular)
    assert subcuenta.moneda == dolar
