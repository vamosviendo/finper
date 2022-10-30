def test_devuelve_true_si_mov_es_traspaso_entre_cuentas_de_distinto_titular(credito):
    assert credito.es_prestamo_o_devolucion()


def test_devuelve_false_si_mov_no_es_traspaso(entrada):
    assert not entrada.es_prestamo_o_devolucion()


def test_devuelve_false_si_cuentas_pertenecen_al_mismo_titular(traspaso):
    assert not traspaso.es_prestamo_o_devolucion()


def test_devuelve_false_si_mov_es_gratis(donacion):
    assert not donacion.es_prestamo_o_devolucion()