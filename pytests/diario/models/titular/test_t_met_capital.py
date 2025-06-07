from diario.models import CuentaInteractiva


def test_devuelve_suma_de_saldos_de_cuentas_de_titular(titular, otro_titular):
    cuenta1 = CuentaInteractiva.crear('cuenta1', 'cta1', saldo=500, titular=titular)
    cuenta2 = CuentaInteractiva.crear('cuenta2', 'cta2', saldo=-120, titular=titular)
    CuentaInteractiva.crear('cuenta_ajena', 'ctaj', saldo=300, titular=otro_titular)

    assert titular.capital() == cuenta1.saldo() + cuenta2.saldo()


def test_devuelve_cero_si_el_titular_no_tiene_cuentas(titular):
    assert titular.capital() == 0


def test_si_recibe_movimiento_devuelve_suma_de_saldos_de_cuentas_de_titular_al_momento_del_movimiento(
        titular, cuenta, cuenta_2, entrada, entrada_otra_cuenta, salida_posterior, entrada_tardia, cuenta_ajena):

    assert titular.capital(movimiento=salida_posterior) == \
           cuenta.saldo(movimiento=salida_posterior) + cuenta_2.saldo(movimiento=salida_posterior)


def test_si_recibe_dia_devuelve_suma_de_saldos_de_cuentas_de_titular_el_dia_dado(
        titular,
        cuenta, cuenta_2, cuenta_ajena,
        entrada, entrada_otra_cuenta, salida_posterior, entrada_posterior_cuenta_ajena, entrada_tardia,
        dia_posterior):
    assert titular.capital(dia=dia_posterior) == cuenta.saldo(dia=dia_posterior) + cuenta_2.saldo(dia=dia_posterior)
