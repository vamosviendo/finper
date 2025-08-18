import pytest

from diario.models import CuentaInteractiva


@pytest.fixture
def subcuentas(cuenta: CuentaInteractiva):
    return cuenta.dividir_entre(
        {'nombre': 'subcuenta 1', 'sk': 'sc1', 'saldo': 30, },
        {'nombre': 'subcuenta 2', 'sk': 'sc2', 'saldo': 1},
        {'nombre': 'subcuenta 3', 'sk': 'sc3'}
    )


def test_devuelve_hijas_de_la_misma_madre(subcuentas):
    for subc in subcuentas[1:]:
        assert subc in subcuentas[0].hermanas()


def test_cuenta_no_se_incluye_a_si_misma_entre_sus_hermanas(subcuentas):
    assert subcuentas[0] not in subcuentas[0].hermanas()


def test_devuelve_none_si_cuenta_no_tiene_madre(cuenta):
    assert cuenta.hermanas() is None
