def test_gt_devuelve_true_si_dia_es_posterior_a_otro(dia, dia_posterior):
    assert dia_posterior > dia

def test_lt_devuelve_true_si_dia_es_anterior_a_otro(dia, dia_posterior):
    assert dia < dia_posterior
