from __future__ import annotations

from diario.models import Movimiento, Cuenta, CuentaInteractiva
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_devuelve_false_si_cuenta_no_es_cuenta_credito(cuenta: Cuenta):
    assert not cuenta.es_cuenta_credito


def test_devuelve_true_si_cuenta_es_cuenta_credito(credito: Movimiento):
    cc2, cc1 = credito.recuperar_cuentas_credito()
    assert cc2.es_cuenta_credito
    assert cc1.es_cuenta_credito
