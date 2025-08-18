from diario.templatetags.movimientos import movs_seleccionados


class TestFilterMovsSeleccionados:
    def test_devuelve_movimientos_de_una_cuenta_en_un_dia(
            self, dia, cuenta, entrada, salida, entrada_anterior, salida_posterior, entrada_otra_cuenta):
        assert list(movs_seleccionados(dia, cuenta)) == [entrada, salida]

    def test_si_cuenta_es_none_devuelve_todos_los_movimientos_del_dia(
            self, dia, entrada, salida, entrada_anterior, salida_posterior, entrada_otra_cuenta):
        assert list(movs_seleccionados(dia, None)) == [entrada, salida, entrada_otra_cuenta]

    def test_devuelve_movimientos_de_un_titular_en_un_dia(
            self, dia, titular, entrada, salida, entrada_anterior, salida_posterior,
            entrada_otra_cuenta, entrada_cuenta_ajena):
        assert list(movs_seleccionados(dia, titular)) == [entrada, salida, entrada_otra_cuenta]

    def test_si_titular_es_none_devuelve_todos_los_movimientos_del_dia(
            self, dia, titular, entrada, salida, entrada_anterior, salida_posterior,
            entrada_otra_cuenta, entrada_cuenta_ajena):
        assert list(movs_seleccionados(dia, None)) == [entrada, salida, entrada_otra_cuenta, entrada_cuenta_ajena]
