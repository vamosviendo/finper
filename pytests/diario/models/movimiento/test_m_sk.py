def test_devuelve_identificador(entrada):
    assert entrada.sk is not None


def test_devuelve_identificador_unico(entrada, salida):
    assert entrada.sk != salida.sk


def test_movimientos_con_el_mismo_orden_dia_tienen_distinto_identificador(entrada, entrada_tardia):
    assert entrada.orden_dia == entrada_tardia.orden_dia
    assert entrada.sk != entrada_tardia.sk


def test_devuelve_str_con_fecha_y_orden_dia(entrada):
    assert type(entrada.sk) == str
    assert \
        entrada.sk == \
        f"{entrada.fecha.year}{entrada.fecha.month:02d}{entrada.fecha.day:02d}{entrada.orden_dia:02d}"
