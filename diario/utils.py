from diario.models import Cuenta


def verificar_saldos():
    ctas_erroneas = []
    for cuenta in Cuenta.todes():
        if not cuenta.saldo_ok():
            ctas_erroneas.append(cuenta)
    return ctas_erroneas


def saldo_general_historico(mov):
    return sum([
        cuenta.saldo_en_mov(mov) for cuenta in Cuenta.filtro(cta_madre=None)
    ])
