import pytest
from django.core.exceptions import ValidationError

from diario.models import Cotizacion


def test_uno_de_ambos_importes_debe_ser_no_nulo(dolar, fecha_posterior):
    cot = Cotizacion(moneda=dolar, fecha=fecha_posterior)
    with pytest.raises(ValidationError, match="Debe ingresar al menos un importe"):
        cot.limpiar()


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_no_admite_importes_negativos(dolar, fecha, tipo):
    cot = Cotizacion(moneda=dolar, fecha=fecha)
    setattr(cot, f"importe_{tipo}", -1)
    with pytest.raises(ValidationError):
        cot.clean_fields()
