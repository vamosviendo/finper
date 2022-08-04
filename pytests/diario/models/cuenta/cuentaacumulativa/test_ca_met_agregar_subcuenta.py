import pytest

from diario.models import Cuenta

pytestmark = pytest.mark.django_db


@pytest.fixture
def subcuenta_agregada(cuenta_acumulativa):
    return cuenta_acumulativa.agregar_subcuenta('subc3', 'sc3')


def test_crea_nueva_subcuenta(cuenta_acumulativa):
    cant_subcuentas = cuenta_acumulativa.subcuentas.count()
    cuenta_acumulativa.agregar_subcuenta('subc3', 'sc3')
    assert cuenta_acumulativa.subcuentas.count() == cant_subcuentas + 1


def test_devuelve_subcuenta_agregada(cuenta_acumulativa):
    subcuenta_agregada = cuenta_acumulativa.agregar_subcuenta('subc3', 'sc3')
    subcuenta = Cuenta.tomar(slug='sc3')
    assert subcuenta_agregada == subcuenta


def test_subcuenta_agregadada_tiene_saldo_cero(subcuenta_agregada):
    assert subcuenta_agregada.saldo == 0


def test_por_defecto_asigna_titular_de_cuenta_madre_a_subcuenta_agregada(subcuenta_agregada, titular):
    assert subcuenta_agregada.titular == titular


def test_permite_asignar_titular_distinto_del_de_cuenta_madre(cuenta_acumulativa, otro_titular):
    subcuenta = cuenta_acumulativa.agregar_subcuenta('subc3', 'sc3', titular=otro_titular)
    assert subcuenta.titular == otro_titular

# PROBAR FIXTURE QUE RESUMA OTROS FIXTURES