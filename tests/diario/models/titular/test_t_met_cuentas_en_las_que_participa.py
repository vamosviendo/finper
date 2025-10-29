def test_incluye_cuentas_propias(titular, cuenta):
    assert cuenta in titular.cuentas_en_las_que_participa()

def test_no_incluye_cuentas_ajenas(titular, cuenta_ajena):
    assert cuenta_ajena not in titular.cuentas_en_las_que_participa()

def test_incluye_cuentas_acumulativas_con_subcuentas_propias_y_ajenas(otro_titular, cuenta_de_dos_titulares):
    assert cuenta_de_dos_titulares in otro_titular.cuentas_en_las_que_participa()

def test_no_incluye_cuentas_acumulativas_sin_subcuentas_propias(otro_titular, cuenta_acumulativa):
    assert cuenta_acumulativa not in otro_titular.cuentas_en_las_que_participa()

def test_incluye_subcuentas_de_cuentas_acumulativas_propias(titular, cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    for sc in [sc1, sc2]:
        assert sc in titular.cuentas_en_las_que_participa()

def test_incluye_solo_subcuentas_propias_de_cuentas_acumulativas_compartidas(otro_titular, cuenta_de_dos_titulares):
    sc1, sc2 = cuenta_de_dos_titulares.subcuentas.all()
    assert sc1 in otro_titular.cuentas_en_las_que_participa()
    assert sc2 not in otro_titular.cuentas_en_las_que_participa()
