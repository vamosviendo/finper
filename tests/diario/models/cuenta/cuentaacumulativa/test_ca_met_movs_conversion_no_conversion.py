from diario.models import Movimiento


class TestsMovConversion:
    def test_devuelve_movimientos_de_traspaso_de_saldo_generados_al_momento_de_la_conversion_en_acumulativa(
            self, cuenta, fecha, fecha_posterior, dicts_subcuentas):
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=cuenta,
            fecha=fecha
        )
        sc1, sc2 = cuenta.dividir_entre(*dicts_subcuentas, fecha=fecha_posterior)
        cuenta_acumulativa = cuenta.tomar_del_sk()

        mov1 = Movimiento.tomar(cta_entrada=sc1)
        mov2 = Movimiento.tomar(cta_entrada=sc2)

        assert list(cuenta_acumulativa.movs_conversion()) == [mov1, mov2]

    def test_si_no_se_generaron_movimientos_al_momento_de_la_conversion_en_acumulativa_devuelve_lista_vacia(
            self, cuenta_acumulativa_saldo_0):
        assert list(cuenta_acumulativa_saldo_0.movs_conversion()) == []


class TestMovsNoConversion:
    def test_devuelve_todos_los_movimientos_de_la_cuenta_excepto_los_de_conversion(
            self, cuenta, entrada, salida, fecha, dicts_subcuentas):
        cuentaacumulativa = cuenta.dividir_y_actualizar(
            *dicts_subcuentas, fecha=fecha)
        assert list(cuentaacumulativa.movs_no_conversion()) == [entrada, salida]
