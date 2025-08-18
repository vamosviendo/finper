def test_toma_valor_de_campo__sk(titular):
    assert titular.sk == titular._sk


def test_puede_fijar_valor_de_campo__sk(titular):
    titular.sk = "nuevaclave"
    assert titular._sk == "nuevaclave"
