import pytest
from django.core.exceptions import FieldError

from diario.models import Movimiento


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_actualiza_subclase_de_cuentas_intervinientes(sentido, mocker, request):
    mock_actualizar_subclase = mocker.patch("diario.models.cuenta.PolymorphModel.actualizar_subclase", autospec=True)
    mov = request.getfixturevalue(sentido)
    cuenta = getattr(mov, f"cta_{sentido}")
    mock_actualizar_subclase.return_value = cuenta

    Movimiento.tomar(pk=mov.pk)
    mock_actualizar_subclase.assert_called_once()
    assert mock_actualizar_subclase.call_args_list[0].args[0].sk == cuenta.sk


def test_permite_tomar_movimiento_por_fecha_y_orden_dia(entrada, salida_posterior, entrada_anterior):
    try:
        mov = Movimiento.tomar(fecha=entrada.fecha, orden_dia=entrada.orden_dia)
    except FieldError:
        raise AssertionError("No permite tomar movimiento por fecha.")

    assert mov.pk == entrada.pk


def test_permite_tomar_movimiento_por_sk(entrada, traspaso, salida_posterior):
    try:
        mov = Movimiento.tomar(sk=entrada.sk)
    except FieldError:
        raise AssertionError("No permite tomar movimiento por sk")

    assert mov.pk == entrada.pk
