import pytest

from diario.models import Movimiento
from utils import errors

pytestmark = pytest.mark.django_db


def test_no_admite_cuentas_acumulativas(cuenta_acumulativa):
    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=errors.CUENTA_ACUMULATIVA_EN_MOVIMIENTO):
        Movimiento.crear(
            'movimiento sobre acum', 100, cta_entrada=cuenta_acumulativa)
