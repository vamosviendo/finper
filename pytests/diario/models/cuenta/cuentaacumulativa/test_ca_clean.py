import pytest
from django.core.exceptions import ValidationError


def test_cuenta_acumulativa_debe_tener_subcuentas(cuenta_acumulativa_saldo_0):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    sc1.delete()
    sc2.delete()
    with pytest.raises(
            ValidationError,
            match='Cuenta acumulativa debe tener subcuentas'):
        cuenta_acumulativa_saldo_0.full_clean()


def test_no_se_puede_asignar_cta_madre_a_cta_interactiva_existente(cuenta_2, cuenta_acumulativa):
    cuenta_2.cta_madre = cuenta_acumulativa

    with pytest.raises(ValidationError):
        cuenta_2.full_clean()


def test_no_se_puede_asignar_cta_madre_a_cta_acumulativa_existente(cuenta_acumulativa, cuenta_acumulativa_saldo_0):
    cuenta_acumulativa.cta_madre = cuenta_acumulativa_saldo_0

    with pytest.raises(ValidationError):
        cuenta_acumulativa.full_clean()
