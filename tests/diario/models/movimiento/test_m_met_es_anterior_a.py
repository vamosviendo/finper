def test_True_si_fecha_es_anterior_a_fecha_de_otro_False_si_es_posterior(entrada, entrada_anterior):
    assert entrada_anterior.es_anterior_a(entrada)
    assert not entrada.es_anterior_a(entrada_anterior)


def test_True_si_fecha_es_igual_y_orden_dia_es_menor_que_el_de_otro_False_si_es_mayor(entrada, salida):
    salida.orden_dia = 0
    salida.save()
    entrada.refresh_from_db(fields=['orden_dia'])
    assert salida.es_anterior_a(entrada)
    assert not entrada.es_anterior_a(salida)
