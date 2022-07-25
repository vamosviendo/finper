import pytest

from diario.models import Saldo

pytestmark = pytest.mark.django_db


def test_devuelve_el_ultimo_saldo_historico_de_la_cuenta(cuenta, entrada, salida_posterior):
    assert (
        cuenta.saldo ==
        Saldo.objects.get(cuenta=cuenta, movimiento=salida_posterior).importe
    )


def test_si_no_encuentra_saldos_en_la_cuenta_devuelve_cero(cuenta):
    # No hay movimientos, por lo tanto no hay saldos
    assert cuenta.saldo == 0.0
