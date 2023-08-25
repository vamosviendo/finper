from diario.models import Cuenta, Movimiento


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


def cuenta2dict(cuenta: Cuenta, movimiento: Movimiento = None):
    """ Prepara los datos de una cuenta para ser mostrados en un template y la
        devuelve en forma de diccionario.
        Si recibe movimiento, devuelve saldo histórico como saldo.
    """
    return {
        'nombre': cuenta.nombre,
        'slug': cuenta.slug,
        'saldo': cuenta.saldo_en_mov(movimiento) if movimiento else cuenta.saldo,
        'es_acumulativa': cuenta.es_acumulativa,
        'subcuentas':
            None if cuenta.es_interactiva else
            [cuenta2dict(x, movimiento) for x in cuenta.subcuentas.all()],
    }
