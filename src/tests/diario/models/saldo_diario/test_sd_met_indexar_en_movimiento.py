from diario.models import SaldoDiario


def test_devuelve_dict_con_cuenta_id_como_clave(cuenta, entrada):
    resultado = SaldoDiario.indexar_en_movimiento([cuenta], entrada)
    assert cuenta.pk in resultado.keys()


def test_devuelve_saldo_al_momento_del_movimiento(cuenta, entrada, salida):
    resultado = SaldoDiario.indexar_en_movimiento([cuenta], entrada)
    assert resultado[cuenta.pk] == cuenta.saldo(movimiento=entrada)


def test_con_multiples_cuentas_devuelve_importe_correcto_por_cuenta(
        cuenta, cuenta_2, entrada, entrada_otra_cuenta):
    resultado = SaldoDiario.indexar_en_movimiento([cuenta, cuenta_2], entrada)
    assert resultado[cuenta.pk] == cuenta.saldo(movimiento=entrada)
    assert resultado[cuenta_2.pk] == cuenta_2.saldo(movimiento=entrada)


def test_si_cuenta_no_tiene_sd_en_dia_del_movimiento_usa_ultimo_sd_anterior(
        cuenta, cuenta_2, entrada, entrada_anterior_otra_cuenta):
    resultado = SaldoDiario.indexar_en_movimiento([cuenta, cuenta_2], entrada)
    assert resultado[cuenta_2.pk] == cuenta_2.saldo(movimiento=entrada)
