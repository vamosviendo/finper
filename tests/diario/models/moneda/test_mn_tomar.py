from django.core.exceptions import FieldError, MultipleObjectsReturned

from diario.models import Moneda


def test_permite_tomar_por_sk_y_devuelve_el_titular_correcto(dolar, peso):
    try:
        m = Moneda.tomar(sk=dolar._sk)
    except (FieldError, MultipleObjectsReturned):
        raise AssertionError("No permite tomar por sk")
    assert m == dolar
