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


def test_si_recibe_dia_y_movimiento_prefiere_movimiento(cuenta, peso, entrada, salida):
    resultado = precalcular_saldos_cuentas(
        [cuenta], [peso], dia=entrada.dia, movimiento=entrada
    )
    assert resultado[cuenta.pk][peso.sk] == float_format(cuenta.saldo(movimiento=entrada))


def test_si_no_recibe_dia_ni_movimiento_eleva_excepcion(cuenta, peso):
    with pytest.raises(ValueError):
        precalcular_saldos_cuentas([cuenta], [peso])
