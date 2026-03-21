from diario.models import SaldoDiario


def test_devuelve_dict_con_cuenta_id_como_clave(cuenta, entrada):
    resultado = SaldoDiario.indexar_por_dia([cuenta], entrada.dia)
    assert cuenta.pk in resultado


def test_devuelve_importe_del_saldo_diario_del_dia(cuenta, entrada, salida_posterior):
    resultado = SaldoDiario.indexar_por_dia([cuenta], entrada.dia)
    assert resultado[cuenta.pk] == cuenta.saldo(dia=entrada.dia)


def test_con_multiples_cuentas_devuelve_importe_correcto_por_cuenta(
        cuenta, cuenta_2, entrada, entrada_otra_cuenta):
    resultado = SaldoDiario.indexar_por_dia([cuenta, cuenta_2], entrada.dia)
    assert resultado[cuenta.pk] == cuenta.saldo(dia=entrada.dia)
    assert resultado[cuenta_2.pk] == cuenta_2.saldo(dia=entrada.dia)


def test_si_cuenta_no_tiene_sd_en_dia_usa_ultimo_sd_anterior(
        cuenta, entrada, dia_posterior):
    resultado = SaldoDiario.indexar_por_dia([cuenta], dia_posterior)
    assert resultado[cuenta.pk] == cuenta.saldo(dia=entrada.dia)


def test_si_cuenta_no_tiene_sd_en_ningun_dia_devuelve_0(
        cuenta, dia):
    resultado = SaldoDiario.indexar_por_dia([cuenta], dia)
    assert resultado.get(cuenta.pk, 0) == 0