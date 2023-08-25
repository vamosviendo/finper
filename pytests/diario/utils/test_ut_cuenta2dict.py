from diario.models import Movimiento
from diario.utils import cuenta2dict


def test_devuelve_un_dict(cuenta):
    assert type(cuenta2dict(cuenta)) == dict


def test_incluye_informacion_de_cuenta(cuenta):
    assert cuenta2dict(cuenta) == {
        'nombre': cuenta.nombre,
        'slug': cuenta.slug,
        'saldo': cuenta.saldo,
        'es_acumulativa': cuenta.es_acumulativa,
        'subcuentas': None
    }


def test_si_se_le_pasa_un_movimiento_toma_saldo_en_movimiento_como_saldo(cuenta, entrada, salida):
    assert cuenta2dict(cuenta, entrada)['saldo'] == cuenta.saldo_en_mov(entrada)


def test_si_cuenta_es_acumulativa_incluye_lista_de_subcuentas(cuenta_acumulativa):
    subcuentas = cuenta2dict(cuenta_acumulativa)['subcuentas']
    assert subcuentas is not None
    assert type(subcuentas) == list


def test_lista_de_subcuentas_incluye_subcuentas_convertidas_a_dict(cuenta_acumulativa):
    assert \
        cuenta2dict(cuenta_acumulativa)['subcuentas'] == \
        [cuenta2dict(x) for x in cuenta_acumulativa.subcuentas.all()]


def test_si_se_pasa_movimiento_y_cuenta_es_acumulativa_subcuentas_incluidas_muestran_saldo_en_mov(
        cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    entrada = Movimiento.crear('Entrada en sc1', 100, cta_entrada=sc1)
    Movimiento.crear('Salida en sc1', 64, cta_salida=sc1)
    for index, sc in enumerate(list(cuenta_acumulativa.subcuentas.all())):
        assert \
            cuenta2dict(cuenta_acumulativa, entrada)['subcuentas'][index]['saldo'] == \
            sc.saldo_en_mov(entrada)