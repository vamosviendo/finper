def test_toma_valor_de_campo__sk(cuenta):
    assert cuenta.sk == cuenta._sk


def test_puede_fijar_valor_de_campo__sk(cuenta):
    cuenta.sk = "nuevaclave"
    assert cuenta._sk == "nuevaclave"
