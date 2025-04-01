import pytest

from diario.models import Movimiento


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_actualiza_subclase_de_cuentas_intervinientes(sentido, mocker, request):
    mock_actualizar_subclase = mocker.patch("diario.models.cuenta.PolymorphModel.actualizar_subclase", autospec=True)
    mov = request.getfixturevalue(sentido)
    cuenta = getattr(mov, f"cta_{sentido}")
    mock_actualizar_subclase.return_value = cuenta

    Movimiento.tomar(pk=mov.pk)
    mock_actualizar_subclase.assert_called_once()
    assert mock_actualizar_subclase.call_args_list[0].args[0].slug == cuenta.slug



