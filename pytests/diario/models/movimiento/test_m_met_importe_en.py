from datetime import date

import pytest

from diario.models import CuentaInteractiva, Movimiento, Moneda


@pytest.fixture
def entrada_en_euros(cuenta_en_euros: CuentaInteractiva, fecha: date, euro: Moneda) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada en euros',
        importe=230,
        cta_entrada=cuenta_en_euros,
        fecha=fecha,
        moneda=euro,
    )


@pytest.mark.parametrize('mov', ['entrada', 'salida', 'traspaso', 'entrada_en_euros'])
def test_devuelve_importe_del_movimiento_en_moneda_dada(mov, dolar, request):
    mov = request.getfixturevalue(mov)
    assert \
        mov.importe_en(dolar) == \
        mov.importe * mov.moneda.cotizacion_en(dolar)
