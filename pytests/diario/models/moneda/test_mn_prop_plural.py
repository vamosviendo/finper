def test_devuelve_valor_del_campo__plural(dolar):
    assert dolar.plural == dolar._plural


def test_si_campo__plural_esta_vacio_devuelve_nombre_en_minusculas_con_una_s_al_final(peso):
    assert peso.plural == peso.nombre.lower() + 's'


def test_guarda_valor_en_campo_plural(peso):
    peso.plural = 'pesotes'
    assert peso._plural == 'pesotes'
