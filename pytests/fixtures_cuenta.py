from datetime import date
from typing import Tuple

import pytest

from diario.models import (
    Titular,
    Cuenta,
    CuentaInteractiva,
    CuentaAcumulativa,
    Movimiento, Moneda
)


@pytest.fixture
def cuenta(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta', sk='c', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_2(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta 2', sk='c2', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_3(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta 3', sk='c3', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_4(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta 4', sk='c4', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_con_saldo(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta_con_saldo',
        sk='ccs',
        saldo=100,
        titular=titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_con_saldo_negativo(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta_con_saldo_negativo',
        sk='ccsn',
        saldo=-100,
        titular=titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_ajena(otro_titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta ajena',
        sk='caj',
        titular=otro_titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_ajena_2(otro_titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta ajena 2',
        sk='caj2',
        titular=otro_titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_gorda(titular_gordo: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta gorda',
        sk='cg',
        titular=titular_gordo,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_acumulativa(cuenta_con_saldo: CuentaInteractiva, fecha: date) -> CuentaAcumulativa:
    return cuenta_con_saldo.dividir_y_actualizar(
        ['subcuenta 1 con saldo', 'scs1', 60],
        ['subcuenta 2 con saldo', 'scs2'],
        fecha=fecha
    )


@pytest.fixture
def cuenta_acumulativa_saldo_0(cuenta: CuentaInteractiva) -> CuentaAcumulativa:
    return cuenta.dividir_y_actualizar(
        ['subcuenta 1 saldo 0', 'sc1', 0],
        ['subcuenta 2 saldo 0', 'sc2'],
        fecha=cuenta.fecha_creacion
    )


@pytest.fixture
def cuenta_acumulativa_saldo_negativo(cuenta_con_saldo_negativo: CuentaInteractiva) -> CuentaAcumulativa:
    return cuenta_con_saldo_negativo.dividir_y_actualizar(
        ['subcuenta 1 saldo negativo', 'scsn1', -10],
        ['subcuenta 2 saldo negativo', 'scsn2'],
        fecha=cuenta_con_saldo_negativo.fecha_creacion
    )


@pytest.fixture
def cuenta_de_dos_titulares(
        titular_gordo: Titular,
        cuenta_ajena: CuentaInteractiva,
        fecha: date,
) -> CuentaAcumulativa:
    return cuenta_ajena.dividir_y_actualizar(
        {
            'nombre': 'Subcuenta otro titular',
            'sk': 'scot',
            'saldo': cuenta_ajena.saldo() - 10
        },
        {
            'nombre': 'Subcuenta titular gordo',
            'sk': 'sctg',
            'saldo': 10,
            'titular': titular_gordo
        },
        fecha=fecha,
    )


@pytest.fixture
def division_gratuita(
        titular_gordo: Titular,
        cuenta_ajena: CuentaInteractiva,
        fecha: date,
) -> CuentaAcumulativa:
    saldo = cuenta_ajena.saldo()
    return cuenta_ajena.dividir_y_actualizar(
        {
            'nombre': 'Subcuenta otro titular',
            'sk': 'scot',
            'saldo': saldo - 10
        },
        {
            'nombre': 'Subcuenta titular gordo',
            'sk': 'sctg',
            'saldo': 10,
            'titular': titular_gordo,
            'esgratis': True
        },
        fecha=fecha,
    )


@pytest.fixture
def cuenta_acumulativa_ajena(cuenta_ajena: CuentaInteractiva) -> CuentaAcumulativa:
    return cuenta_ajena.dividir_y_actualizar(
        ['subcuenta 1 ajena', 'sc1', 0],
        ['subcuenta 2 ajena', 'sc2'],
    )


@pytest.fixture
def subsubcuenta(cuenta_acumulativa: CuentaAcumulativa, fecha: date) -> CuentaInteractiva:
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    ssc11, ssc12 = sc1.dividir_entre(
        {
            'nombre': 'subsubcuenta 1',
            'sk': 'ssc1',
            'saldo': 10,
            'titular': sc1.titular
        },
        {
            'nombre': 'subsubcuenta 2',
            'sk': 'ssc2',
            'titular': sc1.titular
        },
        fecha=fecha,
    )
    return ssc11

@pytest.fixture
def subsubcuenta_2(subsubcuenta: CuentaInteractiva) -> CuentaInteractiva:
    return subsubcuenta.hermanas()[0]


@pytest.fixture
def cuenta_madre_de_cuenta_2(cuenta_2: CuentaInteractiva) -> CuentaAcumulativa:
    return cuenta_2.dividir_y_actualizar(
        ['subcuenta 1 de cuenta 2', 'sc21', 30],
        ['subcuenta 2 de cuenta 2', 'sc22'],
    )


@pytest.fixture
def cuentas_credito(credito: Movimiento) -> Tuple[CuentaInteractiva]:
    return credito.recuperar_cuentas_credito()


@pytest.fixture
def cuenta_credito_acreedor(cuentas_credito: Tuple[CuentaInteractiva]) -> CuentaInteractiva:
    return cuentas_credito[0]


@pytest.fixture
def cuenta_credito_deudor(cuentas_credito: Tuple[CuentaInteractiva]) -> CuentaInteractiva:
    return cuentas_credito[1]


@pytest.fixture
def cuenta_en_dolares(titular: Titular, fecha_temprana: date, dolar: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta en dolares', sk='cd', titular=titular, fecha_creacion=fecha_temprana, moneda=dolar)


@pytest.fixture
def cuenta_en_euros(titular: Titular, fecha: date, euro: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta en euros', sk='ce', titular=titular, fecha_creacion=fecha, moneda=euro)


@pytest.fixture
def cuenta_con_saldo_en_dolares(titular: Titular, fecha_temprana: date, dolar: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta con saldo en dólares',
        sk='ccsd',
        saldo=100,
        titular=titular,
        fecha_creacion=fecha_temprana,
        moneda=dolar,
    )


@pytest.fixture
def cuenta_con_saldo_en_euros(titular: Titular, fecha_temprana: date, euro: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta con saldo en euros',
        sk='ccse',
        saldo=100,
        titular=titular,
        fecha_creacion=fecha_temprana,
        moneda=euro,
    )


@pytest.fixture
def cuenta_con_saldo_en_reales(titular: Titular, fecha: date, real: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta con saldo en reales',
        sk='ccsr',
        saldo=100,
        titular=titular,
        fecha_creacion=fecha,
        moneda=real,
    )


@pytest.fixture
def cuenta_con_saldo_en_yenes(titular: Titular, fecha: date, yen: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta con saldo en yenes',
        sk='ccsy',
        saldo=100,
        titular=titular,
        fecha_creacion=fecha,
        moneda=yen,
    )


@pytest.fixture
def cuenta_acumulativa_en_dolares(cuenta_con_saldo_en_dolares: CuentaInteractiva, fecha: date) -> CuentaAcumulativa:
    return cuenta_con_saldo_en_dolares.dividir_y_actualizar(
        ['subcuenta 1 con saldo en dólares', 'scsd1', 60],
        ['subcuenta 2 con saldo en dólares', 'scsd2'],
        fecha=fecha
    )
