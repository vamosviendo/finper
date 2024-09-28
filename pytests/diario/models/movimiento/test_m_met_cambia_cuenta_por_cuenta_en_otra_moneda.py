import pytest

from diario.models import Movimiento, Moneda


@pytest.fixture
def mov_distintas_monedas_en_euros(mov_distintas_monedas: Movimiento, euro: Moneda) -> Movimiento:
    mov_distintas_monedas.moneda = euro
    mov_distintas_monedas.full_clean()
    mov_distintas_monedas.save()
    return mov_distintas_monedas

class TestMonedaDelMovimientoTrue:

    @pytest.mark.parametrize(
        'campo_cuenta, fixture_movimiento', [
            ('cta_salida', 'mov_distintas_monedas'),
            ('cta_entrada', 'mov_distintas_monedas_en_euros')
        ]
    )
    def test_si_cuenta_en_moneda_del_movimiento_cambia_por_cuenta_en_tercera_moneda_devuelve_true(
            self, campo_cuenta, fixture_movimiento, cuenta_con_saldo_en_reales, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        setattr(movimiento, campo_cuenta, cuenta_con_saldo_en_reales)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda() is True

    @pytest.mark.parametrize(
        'campo_cuenta, fixture_movimiento, fixture_cuenta', [
            ('cta_entrada', 'mov_distintas_monedas_en_euros', 'cuenta_en_dolares'),
            ('cta_salida', 'mov_distintas_monedas', 'cuenta_en_euros')
        ]
    )
    def test_si_cuenta_en_moneda_del_movimiento_cambia_por_cuenta_en_otra_moneda_devuelve_true(
            self, campo_cuenta, fixture_movimiento, fixture_cuenta, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        cuenta_nueva = request.getfixturevalue(fixture_cuenta)
        setattr(movimiento, campo_cuenta, cuenta_nueva)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda() is True

    @pytest.mark.parametrize(
        'campo_cuenta, fixture_movimiento', [
            ('cta_salida', 'mov_distintas_monedas'),
            ('cta_entrada', 'mov_distintas_monedas_en_euros')
        ]
    )
    def test_si_cuenta_en_moneda_del_movimiento_no_cambia_devuelve_false(
            self, campo_cuenta, fixture_movimiento, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda() is False

    @pytest.mark.parametrize(
        'campo_cuenta, fixture_movimiento, fixture_cuenta', [
            ('cta_entrada', 'mov_distintas_monedas_en_euros', 'cuenta_en_euros'),
            ('cta_salida', 'mov_distintas_monedas', 'cuenta_en_dolares'),
        ]
    )
    def test_si_cuenta_en_moneda_del_movimiento_cambia_por_cuenta_en_la_misma_moneda_devuelve_false(
            self, campo_cuenta, fixture_movimiento, fixture_cuenta, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        cuenta_nueva = request.getfixturevalue(fixture_cuenta)
        setattr(movimiento, campo_cuenta, cuenta_nueva)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda() is False

    @pytest.mark.parametrize(
        'campo_cuenta, fixture_movimiento', [
            ('cta_entrada', 'mov_distintas_monedas'),
            ('cta_salida', 'mov_distintas_monedas_en_euros')
        ]
    )
    def test_si_cuenta_en_otra_moneda_cambia_y_cuenta_en_moneda_del_movimiento_no_devuelve_false(
            self, campo_cuenta, fixture_movimiento, cuenta_con_saldo_en_reales, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        setattr(movimiento, campo_cuenta, cuenta_con_saldo_en_reales)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda() is False


class TestMonedaDelMovimientoFalse:

    @pytest.mark.parametrize('campo_cuenta, fixture_movimiento', [
        ('cta_entrada', 'mov_distintas_monedas'),
        ('cta_salida', 'mov_distintas_monedas_en_euros')
    ])
    def test_si_cuenta_en_otra_moneda_cambia_por_cuenta_en_tercera_moneda_devuelve_true(
            self, campo_cuenta, fixture_movimiento, cuenta_con_saldo_en_reales, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        setattr(movimiento, campo_cuenta, cuenta_con_saldo_en_reales)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) is True

    @pytest.mark.parametrize('campo_cuenta, fixture_movimiento, fixture_cuenta', [
        ('cta_entrada', 'mov_distintas_monedas', 'cuenta_en_dolares'),
        ('cta_salida', 'mov_distintas_monedas_en_euros', 'cuenta_en_euros')
    ])
    def test_si_cuenta_en_otra_moneda_cambia_por_cuenta_en_moneda_del_movimiento_devuelve_true(
            self, campo_cuenta, fixture_movimiento, fixture_cuenta, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        cuenta_nueva = request.getfixturevalue(fixture_cuenta)
        setattr(movimiento, campo_cuenta, cuenta_nueva)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) is True

    @pytest.mark.parametrize('campo_cuenta, fixture_movimiento', [
        ('cta_entrada', 'mov_distintas_monedas'),
        ('cta_salida', 'mov_distintas_monedas_en_euros')
    ])
    def test_si_cuenta_en_otra_moneda_no_cambia_devuelve_false(
            self, campo_cuenta, fixture_movimiento, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) is False

    @pytest.mark.parametrize('campo_cuenta, fixture_movimiento, fixture_cuenta', [
        ('cta_entrada', 'mov_distintas_monedas', 'cuenta_en_euros'),
        ('cta_salida', 'mov_distintas_monedas_en_euros', 'cuenta_en_dolares'),
    ])
    def test_si_cuenta_en_otra_moneda_cambia_por_cuenta_en_la_misma_otra_moneda_devuelve_false(
            self, campo_cuenta, fixture_movimiento, fixture_cuenta, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        cuenta_nueva = request.getfixturevalue(fixture_cuenta)
        setattr(movimiento, campo_cuenta, cuenta_nueva)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) is False

    @pytest.mark.parametrize('campo_cuenta, fixture_movimiento', [
        ('cta_entrada', 'mov_distintas_monedas_en_euros'),
        ('cta_salida', 'mov_distintas_monedas')
    ])
    def test_si_cuenta_en_moneda_del_movimiento_cambia_y_cuenta_en_otra_moneda_no_devuelve_false(
            self, campo_cuenta, fixture_movimiento, cuenta_con_saldo_en_reales, request):
        movimiento = request.getfixturevalue(fixture_movimiento)
        setattr(movimiento, campo_cuenta, cuenta_con_saldo_en_reales)
        assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) is False
