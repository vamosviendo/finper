import pytest


def test_devuelve_dia_anterior_a_self(dia, dia_anterior, dia_temprano):
    assert dia.anterior() == dia_anterior

@pytest.mark.parametrize("fixt_ente", ["titular", "cuenta"])
def test_si_recibe_titular_o_cuenta_devuelve_dia_anterior_entre_los_del_titular_o_cuenta(
        fixt_ente, cuenta_ajena, entrada, entrada_posterior_cuenta_ajena, entrada_temprana, request):
    ente = request.getfixturevalue(fixt_ente)
    dia = entrada.dia
    dia_anterior_ente = entrada_temprana.dia

    assert dia.anterior(ente=ente) == dia_anterior_ente
