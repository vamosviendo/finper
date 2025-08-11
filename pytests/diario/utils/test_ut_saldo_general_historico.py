from datetime import timedelta

import pytest

from diario.models import Movimiento
from diario.utils.utils_saldo import saldo_general_historico
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_devuelve_suma_de_saldos_historicos_de_cuentas_al_momento_del_movimiento(
        entrada, entrada_posterior_otra_cuenta, salida_tardia_tercera_cuenta):
    assert \
        saldo_general_historico(entrada) == \
        entrada.cta_entrada.saldo(movimiento=entrada)
    assert \
        saldo_general_historico(entrada_posterior_otra_cuenta) == \
            entrada.cta_entrada.saldo(movimiento=entrada_posterior_otra_cuenta) + \
            entrada_posterior_otra_cuenta.cta_entrada.saldo(movimiento=entrada_posterior_otra_cuenta)
    assert \
        saldo_general_historico(salida_tardia_tercera_cuenta) == \
            saldo_general_historico(entrada_posterior_otra_cuenta) + \
        salida_tardia_tercera_cuenta.cta_salida.saldo(movimiento=salida_tardia_tercera_cuenta)


def test_suma_una_sola_vez_saldo_de_cuentas_acumulativas(
        cuenta, entrada_posterior_otra_cuenta, salida_tardia_tercera_cuenta, fecha_tardia_plus):
    cuenta = dividir_en_dos_subcuentas(
        cuenta, saldo=3, fecha= fecha_tardia_plus)
    mov = Movimiento.crear(
        'Ultimo mov',
        importe=5,
        cta_entrada=salida_tardia_tercera_cuenta.cta_salida,
        fecha=fecha_tardia_plus+timedelta(1)
    )
    assert saldo_general_historico(mov) == sum([
        c.saldo(movimiento=mov) for c in (
            cuenta,
            entrada_posterior_otra_cuenta.cta_entrada,
            salida_tardia_tercera_cuenta.cta_salida,
        )
    ])


@pytest.mark.parametrize("compra", [True, False])
def test_devuelve_importe_en_moneda_dada(
        cuenta, entrada, dolar, compra):
    assert \
        saldo_general_historico(entrada, moneda=dolar, compra=compra) == \
        round(saldo_general_historico(entrada) / dolar.cotizacion_al(entrada.dia.fecha, compra=compra), 2)
