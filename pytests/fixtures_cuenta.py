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
        nombre='cuenta', slug='c', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_2(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta 2', slug='c2', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_3(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta 3', slug='c3', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_4(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta 4', slug='c4', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_con_saldo(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta_con_saldo',
        slug='ccs',
        saldo=100,
        titular=titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_con_saldo_negativo(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta_con_saldo_negativo',
        slug='ccsn',
        saldo=-100,
        titular=titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_ajena(otro_titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta ajena',
        slug='caj',
        titular=otro_titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_ajena_2(otro_titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta ajena 2',
        slug='caj2',
        titular=otro_titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_gorda(titular_gordo: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta gorda',
        slug='cg',
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
def cuenta_de_dos_titulares(
        titular_gordo: Titular,
        cuenta_ajena: CuentaInteractiva,
) -> CuentaAcumulativa:
    return cuenta_ajena.dividir_y_actualizar(
        {
            'nombre': 'Subcuenta otro titular',
            'slug': 'scot',
            'saldo': cuenta_ajena.saldo - 10
        },
        {
            'nombre': 'Subcuenta titular gordo',
            'slug': 'sctg',
            'saldo': 10,
            'titular': titular_gordo
        }
    )


@pytest.fixture
def cuenta_acumulativa_ajena(cuenta_ajena: CuentaInteractiva) -> CuentaAcumulativa:
    return cuenta_ajena.dividir_y_actualizar(
        ['subcuenta 1 ajena', 'sc1', 0],
        ['subcuenta 2 ajena', 'sc2'],
    )


@pytest.fixture
def subsubcuenta(cuenta_acumulativa: CuentaAcumulativa) -> CuentaInteractiva:
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    ssc11, ssc12 = sc1.dividir_entre(
        {
            'nombre': 'subsubuenta 1',
            'slug': 'ssc1',
            'saldo': 10,
            'titular': sc1.titular
        },
        {
            'nombre': 'subsubcuenta 2',
            'slug': 'ssc2',
            'titular': sc1.titular
        }
    )
    return ssc11


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
def cuenta_en_dolares(titular: Titular, fecha: date, dolar: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta en dolares', slug='cd', titular=titular, fecha_creacion=fecha, moneda=dolar)


@pytest.fixture
def cuenta_en_euros(titular: Titular, fecha: date, euro: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta en euros', slug='ce', titular=titular, fecha_creacion=fecha, moneda=euro)
