from django.core.exceptions import FieldError, MultipleObjectsReturned

from diario.models import Titular


def test_permite_tomar_por_sk_y_devuelve_el_titular_correcto(titular, otro_titular):
    try:
        t = Titular.tomar(sk=titular._sk)
    except (FieldError, MultipleObjectsReturned):
        raise AssertionError("No permite tomar por sk")
    assert t == titular
