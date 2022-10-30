import pytest

from diario.models import Saldo


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_viene_de_entrada_devuelve_true_y_viene_de_salida_false_si_la_cuenta_es_cta_entrada_de_su_movimiento_y_viceversa(
        sentido, request):
    mov = request.getfixturevalue(sentido)
    contrasentido = 'salida' if sentido == 'entrada' else 'entrada'
    saldo = Saldo.objects.get(
        cuenta=getattr(mov, f'cta_{sentido}'),
        movimiento=mov
    )
    assert getattr(saldo, f'viene_de_{sentido}')
    assert not getattr(saldo, f'viene_de_{contrasentido}')
