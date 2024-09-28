import pytest

from diario.models import Movimiento, Moneda


@pytest.fixture
def mov_distintas_monedas_en_euros(mov_distintas_monedas: Movimiento, euro: Moneda) -> Movimiento:
    mov_distintas_monedas.moneda = euro
    mov_distintas_monedas.full_clean()
    mov_distintas_monedas.save()
    return mov_distintas_monedas

@pytest.mark.parametrize(
    'campo_cuenta, fixture_movimiento, mon_mov', [
        ('cta_entrada', 'mov_distintas_monedas_en_euros', True),
        ('cta_salida', 'mov_distintas_monedas', True),
        ('cta_entrada', 'mov_distintas_monedas', False),
        ('cta_salida', 'mov_distintas_monedas_en_euros', False)
    ]
)
def test_si_cuenta_cambia_por_cuenta_en_tercera_moneda_devuelve_true(
        campo_cuenta, fixture_movimiento, mon_mov, cuenta_con_saldo_en_reales, request):
    movimiento = request.getfixturevalue(fixture_movimiento)
    setattr(movimiento, campo_cuenta, cuenta_con_saldo_en_reales)
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is True

@pytest.mark.parametrize(
    'campo_cuenta, fixture_movimiento, fixture_cuenta, mon_mov', [
        ('cta_entrada', 'mov_distintas_monedas_en_euros', 'cuenta_en_dolares', True),
        ('cta_salida', 'mov_distintas_monedas', 'cuenta_en_euros', True),
        ('cta_entrada', 'mov_distintas_monedas', 'cuenta_en_dolares', False),
        ('cta_salida', 'mov_distintas_monedas_en_euros', 'cuenta_en_euros', False)
    ]
)
def test_si_cuenta_cambia_por_cuenta_en_moneda_de_la_otra_cuenta_devuelve_true(
        campo_cuenta, fixture_movimiento, fixture_cuenta, mon_mov, request):
    movimiento = request.getfixturevalue(fixture_movimiento)
    cuenta_nueva = request.getfixturevalue(fixture_cuenta)
    setattr(movimiento, campo_cuenta, cuenta_nueva)
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is True

@pytest.mark.parametrize(
    'campo_cuenta, fixture_movimiento, mon_mov', [
        ('cta_salida', 'mov_distintas_monedas', True),
        ('cta_entrada', 'mov_distintas_monedas_en_euros', True),
        ('cta_entrada', 'mov_distintas_monedas', False),
        ('cta_salida', 'mov_distintas_monedas_en_euros', False)
    ]
)
def test_si_cuenta_no_cambia_devuelve_false(campo_cuenta, fixture_movimiento, mon_mov, request):
    movimiento = request.getfixturevalue(fixture_movimiento)
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is False

@pytest.mark.parametrize(
    'campo_cuenta, fixture_movimiento, fixture_cuenta, mon_mov', [
        ('cta_entrada', 'mov_distintas_monedas_en_euros', 'cuenta_en_euros', True),
        ('cta_salida', 'mov_distintas_monedas', 'cuenta_en_dolares', True),
        ('cta_entrada', 'mov_distintas_monedas', 'cuenta_en_euros', False),
        ('cta_salida', 'mov_distintas_monedas_en_euros', 'cuenta_en_dolares', False),
    ]
)
def test_si_cuenta_cambia_por_cuenta_en_la_misma_moneda_devuelve_false(
        campo_cuenta, fixture_movimiento, fixture_cuenta, mon_mov, request):
    movimiento = request.getfixturevalue(fixture_movimiento)
    cuenta_nueva = request.getfixturevalue(fixture_cuenta)
    setattr(movimiento, campo_cuenta, cuenta_nueva)
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is False

@pytest.mark.parametrize(
    'campo_cuenta, fixture_movimiento, mon_mov', [
        ('cta_entrada', 'mov_distintas_monedas', True),
        ('cta_salida', 'mov_distintas_monedas_en_euros', True),
        ('cta_entrada', 'mov_distintas_monedas_en_euros', False),
        ('cta_salida', 'mov_distintas_monedas', False)
    ]
)
def test_si_cuenta_opuesta_cambia_y_cuenta_no_devuelve_false(
        campo_cuenta, fixture_movimiento, cuenta_con_saldo_en_reales, mon_mov, request):
    movimiento = request.getfixturevalue(fixture_movimiento)
    setattr(movimiento, campo_cuenta, cuenta_con_saldo_en_reales)
    assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=mon_mov) is False
