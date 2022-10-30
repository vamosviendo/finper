import pytest
from django.core.exceptions import ValidationError

from diario.models import Saldo


def test_no_admite_mas_de_un_saldo_por_cuenta_en_cada_movimiento(entrada):
    saldo = Saldo()
    saldo.cuenta = entrada.cta_entrada
    saldo.movimiento = entrada
    saldo.importe = 15

    with pytest.raises(ValidationError):
        saldo.full_clean()
