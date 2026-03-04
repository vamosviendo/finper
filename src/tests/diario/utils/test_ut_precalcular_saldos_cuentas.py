import pytest

from diario.utils.utils_saldo import precalcular_saldos_cuentas
from utils.numeros import float_format


def test_devuelve_dict_con_pk_de_cuenta_como_clave(cuenta, entrada, peso):
    dia = entrada.dia
    resultado = precalcular_saldos_cuentas([cuenta], [peso], dia)
    assert cuenta.pk in resultado.keys()


def test_devuelve_dict_con_sk_de_moneda_como_subclave(cuenta, entrada, peso):
    dia = entrada.dia
    resultado = precalcular_saldos_cuentas([cuenta], [peso], dia)
    assert peso.sk in resultado[cuenta.pk].keys()

def test_devuelve_saldo_formateado_con_dos_decimales(cuenta, entrada, peso):
    dia = entrada.dia
    resultado = precalcular_saldos_cuentas([cuenta], [peso], dia)
    assert resultado[cuenta.pk][peso.sk] == float_format(cuenta.saldo(dia=dia))


# Saldo correcto según el día

def test_devuelve_saldo_de_cuenta_en_el_dia_dado(cuenta, entrada, salida_posterior, peso):
    dia_entrada = entrada.dia
    resultado = precalcular_saldos_cuentas([cuenta], [peso], dia_entrada)
    assert resultado[cuenta.pk][peso.sk] == float_format(cuenta.saldo(dia=dia_entrada))

def test_si_cuenta_no_tiene_saldo_diario_en_el_dia_dado_usa_ultimo_saldo_diario_anterior(
        cuenta, entrada, dia_posterior, peso):
    # dia_posterior no tiene movimientos de cuenta, pero el saldo anterior existe
    resultado = precalcular_saldos_cuentas([cuenta], [peso], dia_posterior)
    assert resultado[cuenta.pk][peso.sk] == float_format(cuenta.saldo(dia=entrada.dia))

def test_si_cuenta_no_tiene_ningun_saldo_diario_anterior_devuelve_cero(cuenta, dia, peso):
    # dia existe pero cuenta no tiene ningún movimiento
    resultado = precalcular_saldos_cuentas([cuenta], [peso], dia)
    assert resultado[cuenta.pk][peso.sk] == float_format(0)


# Múltiples cuentas

def test_devuelve_saldo_correcto_para_cada_cuenta_en_lista(
        cuenta, cuenta_2, entrada, entrada_otra_cuenta, peso):
    dia = entrada.dia
    resultado = precalcular_saldos_cuentas([cuenta, cuenta_2], [peso], dia)
    assert resultado[cuenta.pk][peso.sk] == float_format(cuenta.saldo(dia=dia))
    assert resultado[cuenta_2.pk][peso.sk] == float_format(cuenta_2.saldo(dia=dia))


# Monedas

def test_cuenta_en_moneda_base_devuelve_saldo_sin_conversion(cuenta, entrada, peso, dolar):
    dia = entrada.dia
    resultado = precalcular_saldos_cuentas([cuenta], [peso], dia)
    assert resultado[cuenta.pk][peso.sk] == float_format(cuenta.saldo(dia=dia))


def test_cuenta_en_moneda_no_base_devuelve_saldo_convertido_a_moneda_base(
        cuenta_con_saldo_en_dolares, peso, dolar, dia):
    resultado = precalcular_saldos_cuentas(
        [cuenta_con_saldo_en_dolares], [peso], dia
    )
    saldo_esperado = float_format(
        cuenta_con_saldo_en_dolares.saldo(dia=dia, moneda=peso, compra=True)
    )
    assert resultado[cuenta_con_saldo_en_dolares.pk][peso.sk] == saldo_esperado


def test_si_no_hay_cotizaciones_para_la_moneda_dada_devuelve_saldo_sin_conversion(
        cuenta_con_saldo_en_dolares, peso, dolar, dia):
    dolar.cotizaciones.all().delete()
    resultado = precalcular_saldos_cuentas(
        [cuenta_con_saldo_en_dolares], [peso], dia
    )
    assert resultado[cuenta_con_saldo_en_dolares.pk][peso.sk] == \
           float_format(cuenta_con_saldo_en_dolares.saldo(dia=dia))


def test_si_recibe_movimiento_devuelve_saldos_al_momento_del_movimiento(cuenta, peso, entrada, salida_posterior):
    resultado = precalcular_saldos_cuentas([cuenta], [peso], movimiento=entrada)
    assert resultado[cuenta.pk][peso.sk] == float_format(cuenta.saldo(movimiento=entrada))


def test_saldo_en_movimiento_difiere_del_saldo_en_movimiento_posterior(
        cuenta, entrada, salida, peso):
    resultado_entrada = precalcular_saldos_cuentas(
        [cuenta], [peso], movimiento=entrada
    )
    resultado_salida = precalcular_saldos_cuentas(
        [cuenta], [peso], movimiento=salida
    )
    assert resultado_entrada[cuenta.pk][peso.sk] != resultado_salida[cuenta.pk][peso.sk]


def test_si_movimiento_no_es_el_ultimo_del_dia_el_saldo_difiere_del_saldo_diario(
        cuenta, entrada, salida, peso):
    # Ambos en el mismo día: saldo en entrada != saldo al final del día
    assert cuenta.saldo(movimiento=entrada) != cuenta.saldo(dia=entrada.dia)
    resultado_mov = precalcular_saldos_cuentas([cuenta], [peso], movimiento=entrada)
    resultado_dia = precalcular_saldos_cuentas([cuenta], [peso], dia=entrada.dia)
    assert resultado_mov[cuenta.pk][peso.sk] != resultado_dia[cuenta.pk][peso.sk]


def test_si_recibe_dia_y_movimiento_prefiere_movimiento(cuenta, peso, entrada, salida):
    resultado = precalcular_saldos_cuentas(
        [cuenta], [peso], dia=entrada.dia, movimiento=entrada
    )
    assert resultado[cuenta.pk][peso.sk] == float_format(cuenta.saldo(movimiento=entrada))


def test_si_no_recibe_dia_ni_movimiento_eleva_excepcion(cuenta, peso):
    with pytest.raises(ValueError):
        resultado = precalcular_saldos_cuentas([cuenta], [peso])
