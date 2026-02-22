import pytest


@pytest.mark.parametrize('cuenta', ['cuenta_en_dolares', 'cuenta_en_euros'])
def test_devuelve_cotizacion_de_la_moneda_de_la_cuenta(cuenta, request):
    cuenta = request.getfixturevalue(cuenta)
    assert cuenta.cotizacion == cuenta.moneda.cotizacion
