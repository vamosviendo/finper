from datetime import timedelta

from diario.models import Saldo, Movimiento
from diario.utils import saldo_general_historico
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_devuelve_suma_de_saldos_historicos_de_cuentas_al_momento_del_movimiento(
        entrada, entrada_posterior_otra_cuenta, salida_tardia_tercera_cuenta):
    assert \
        saldo_general_historico(entrada) == \
        Saldo.tomar(cuenta=entrada.cta_entrada, movimiento=entrada).importe
    assert \
        saldo_general_historico(entrada_posterior_otra_cuenta) == \
            Saldo.tomar(
                cuenta=entrada.cta_entrada,
                movimiento=entrada_posterior_otra_cuenta
            ).importe + \
            Saldo.tomar(
                cuenta=entrada_posterior_otra_cuenta.cta_entrada,
                movimiento=entrada_posterior_otra_cuenta
            ).importe
    assert \
        saldo_general_historico(salida_tardia_tercera_cuenta) == \
            saldo_general_historico(entrada_posterior_otra_cuenta) + \
            Saldo.tomar(
                cuenta=salida_tardia_tercera_cuenta.cta_salida,
                movimiento=salida_tardia_tercera_cuenta
            ).importe


def test_suma_una_sola_vez_saldo_de_cuentas_acumulativas(
        cuenta, entrada_posterior_otra_cuenta, salida_tardia_tercera_cuenta, fecha_tardia_plus):
    dividir_en_dos_subcuentas(
        cuenta, saldo=3, fecha= fecha_tardia_plus)
    mov = Movimiento.crear(
        'Ultimo mov',
        importe=5,
        cta_entrada=salida_tardia_tercera_cuenta.cta_salida,
        fecha=fecha_tardia_plus+timedelta(1)
    )
    assert saldo_general_historico(mov) == sum([
        Saldo.tomar(cuenta=cuenta, movimiento=mov).importe,
        Saldo.tomar(
            cuenta=entrada_posterior_otra_cuenta.cta_entrada,
            movimiento=mov
        ).importe,
        Saldo.tomar(
            cuenta=salida_tardia_tercera_cuenta.cta_salida,
            movimiento=mov
        ).importe,
    ])
