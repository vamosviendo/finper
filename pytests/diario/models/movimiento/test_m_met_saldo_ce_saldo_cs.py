import pytest


def test_devuelven_saldo_de_cta_entrada_y_cta_salida_respectivamente_al_momento_del_movimiento(traspaso):
    assert traspaso.saldo_ce() == traspaso.cta_entrada.saldo_set.get(movimiento=traspaso)
    assert traspaso.saldo_cs() == traspaso.cta_salida.saldo_set.get(movimiento=traspaso)


def test_saldo_ce_tira_error_si_mov_no_tiene_cta_entrada(salida):
    with pytest.raises(
            AttributeError,
            match=f'Movimiento "{salida.concepto}" no tiene cuenta de entrada'
    ):
        salida.saldo_ce()

def test_saldo_cs_tira_error_si_mov_no_tiene_cta_salida(entrada):
    with pytest.raises(
        AttributeError,
        match=f'Movimiento "{entrada.concepto}" no tiene cuenta de salida'
    ):
        entrada.saldo_cs()
