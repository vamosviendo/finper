import pytest

from diario.models import Cotizacion
from utils.varios import el_que_no_es


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_si_hay_un_solo_importe_guarda_el_mismo_valor_en_el_otro(tipo, dolar, fecha_posterior):
    tipo_opuesto = el_que_no_es(tipo, "compra", "venta")
    cot = Cotizacion(**{
        "moneda": dolar,
        "fecha": fecha_posterior,
        f"importe_{tipo}": 5.41
    })
    cot.full_clean()
    cot.save()

    assert getattr(cot, f"importe_{tipo_opuesto}") == 5.41
