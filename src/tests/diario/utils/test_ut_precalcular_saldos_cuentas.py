import pytest

from diario.models import CuentaAcumulativa
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


def test_incluye_cuentas_acumulativas_si_recibe_dia(
        cuenta, cuenta_2, cuenta_acumulativa, dia, peso):
    saldos= precalcular_saldos_cuentas([cuenta, cuenta_acumulativa], [peso], dia=dia)
    importe_mostrado = float(
        saldos[cuenta_acumulativa.pk][peso.sk].replace(',', '.')
    )
    assert importe_mostrado == cuenta_acumulativa.saldo(dia=dia)


def test_incluye_cuentas_acumulativas_si_recibe_movimiento(
        cuenta, cuenta_2, cuenta_acumulativa, entrada, peso):
    saldos= precalcular_saldos_cuentas(
        [cuenta, cuenta_acumulativa], [peso], movimiento=entrada
    )
    importe_mostrado = float(
        saldos[cuenta_acumulativa.pk][peso.sk].replace(',', '.')
    )
    assert importe_mostrado == cuenta_acumulativa.saldo(movimiento=entrada)


def test_precalcular_con_movimiento_no_llama_cuenta_saldo(
    cuenta, cuenta_acumulativa, dia, entrada, salida, peso, mocker
):
    mock_saldo = mocker.patch.object(CuentaAcumulativa, 'saldo')
    precalcular_saldos_cuentas(
        [cuenta, cuenta_acumulativa], [peso], movimiento=salida
    )
    mock_saldo.assert_not_called()
