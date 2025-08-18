def test_toma_valor_de_campo__sk(dolar):
    assert dolar.sk == dolar._sk


def test_puede_fijar_valor_de_campo__sk(dolar):
    dolar.sk = "nuevaclave"
    assert dolar._sk == "nuevaclave"
