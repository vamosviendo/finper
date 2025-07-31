from django.core.management import call_command


def test_reemplaza_en_todos_los_movimientos_de_cuenta_origen_a_esta_por_cuenta_destino(
        cuenta, cuenta_3, entrada, traspaso, salida, salida_posterior, entrada_tardia):
    movimientos = [m.pk for m in cuenta.movs()]
    call_command("pasar_movimientos", cuenta.sk, cuenta_3.sk)
    assert [m.pk for m in cuenta_3.movs()] == movimientos
    assert not cuenta.movs().exists()
