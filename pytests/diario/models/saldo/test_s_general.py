from diario.models import Saldo


def test_saldos_se_ordenan_por_movimiento(cuenta, entrada_tardia, salida_posterior, entrada):
    saldo_tardio = Saldo.objects.get(cuenta=cuenta, movimiento=entrada_tardia)
    saldo_posterior = Saldo.objects.get(cuenta=cuenta, movimiento=salida_posterior)
    saldo = Saldo.objects.get(cuenta=cuenta, movimiento=entrada)

    assert list(Saldo.todes()) == [saldo, saldo_posterior, saldo_tardio]
