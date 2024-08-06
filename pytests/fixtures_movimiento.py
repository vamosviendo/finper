from datetime import date
from random import randint

import pytest
from django.db.models import QuerySet

from diario.models import CuentaInteractiva, Dia, Movimiento, Moneda, CuentaAcumulativa
from utils.helpers_tests import cambiar_fecha_creacion, dividir_en_dos_subcuentas


@pytest.fixture
def entrada_temprana(cuenta: CuentaInteractiva, dia_temprano: Dia) -> Movimiento:
    cambiar_fecha_creacion(cuenta, dia_temprano.fecha)
    return Movimiento.crear(
        concepto='Entrada temprana', importe=47,
        cta_entrada=cuenta, dia=dia_temprano
    )


@pytest.fixture
def entrada_anterior(cuenta: CuentaInteractiva, dia_anterior: Dia) -> Movimiento:
    cambiar_fecha_creacion(cuenta, dia_anterior.fecha)
    return Movimiento.crear(
        concepto='Entrada anterior', importe=3,
        cta_entrada=cuenta, dia=dia_anterior
    )


@pytest.fixture
def entrada(cuenta: CuentaInteractiva, dia: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada', importe=100, cta_entrada=cuenta, dia=dia
    )


@pytest.fixture
def salida(cuenta: CuentaInteractiva, dia: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Salida', importe=115, cta_salida=cuenta, dia=dia
    )


@pytest.fixture
def entrada_cuenta_ajena(cuenta_ajena: CuentaInteractiva, dia: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada cuenta ajena', importe=849, cta_entrada=cuenta_ajena, dia=dia
    )


@pytest.fixture
def traspaso(cuenta: CuentaInteractiva, cuenta_2: CuentaInteractiva, dia: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Traspaso', importe=2,
        cta_entrada=cuenta, cta_salida=cuenta_2,
        dia=dia
    )


@pytest.fixture
def entrada_otra_cuenta(cuenta_2: CuentaInteractiva, dia: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada', importe=486, cta_entrada=cuenta_2, dia=dia
    )


@pytest.fixture
def entrada_posterior_otra_cuenta(cuenta_2: CuentaInteractiva, dia_posterior: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada posterior otra cuenta', importe=50,
        cta_entrada=cuenta_2, dia=dia_posterior
    )


@pytest.fixture
def entrada_posterior_cuenta_ajena(cuenta_ajena: CuentaInteractiva, dia_posterior: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada posterior cuenta ajena', importe=60,
        cta_entrada=cuenta_ajena, dia=dia_posterior
    )


@pytest.fixture
def salida_posterior(cuenta: CuentaInteractiva, dia_posterior: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Salida posterior',
        importe=40,
        cta_salida=cuenta,
        dia=dia_posterior
    )


@pytest.fixture
def traspaso_posterior(cuenta: CuentaInteractiva, cuenta_2: CuentaInteractiva, dia_posterior: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Traspaso posterior', importe=70,
        cta_entrada=cuenta_2, cta_salida=cuenta,
        dia=dia_posterior,
    )


@pytest.fixture
def entrada_tardia(cuenta: CuentaInteractiva, dia_tardio: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada tardía',
        importe=80,
        cta_entrada=cuenta,
        dia=dia_tardio,
    )


@pytest.fixture
def salida_tardia_tercera_cuenta(cuenta_3: CuentaInteractiva, dia_tardio: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Salida tardía tercera cuenta',
        importe=9648.22,
        cta_salida=cuenta_3,
        dia=dia_tardio,
    )


@pytest.fixture
def entrada_con_ca(entrada: Movimiento) -> Movimiento:
    dividir_en_dos_subcuentas(entrada.cta_entrada)
    entrada.refresh_from_db()
    return entrada


@pytest.fixture
def salida_con_ca(salida: Movimiento) -> Movimiento:
    dividir_en_dos_subcuentas(salida.cta_salida)
    salida.refresh_from_db()
    return salida


@pytest.fixture
def traspaso_con_cta_entrada_a(traspaso: Movimiento) -> Movimiento:
    dividir_en_dos_subcuentas(traspaso.cta_entrada)
    traspaso.refresh_from_db()
    return traspaso


@pytest.fixture
def traspaso_con_cta_salida_a(traspaso: Movimiento) -> Movimiento:
    dividir_en_dos_subcuentas(traspaso.cta_salida)
    traspaso.refresh_from_db()
    return traspaso


@pytest.fixture
def credito(cuenta: CuentaInteractiva, cuenta_ajena: CuentaInteractiva, dia: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto='Crédito',
        importe=128,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
        dia=dia,
    )


@pytest.fixture
def donacion(cuenta: CuentaInteractiva, cuenta_ajena: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Donación',
        importe=253,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
        fecha=fecha,
        esgratis=True,
    )


@pytest.fixture
def credito_entre_subcuentas(cuenta_de_dos_titulares: CuentaAcumulativa, fecha: date) -> Movimiento:
    scot, sctg = cuenta_de_dos_titulares.subcuentas.all()
    return Movimiento.crear(
        concepto='Crédito entre subcuentas',
        importe=50,
        cta_entrada=scot,
        cta_salida=sctg,
    )


@pytest.fixture
def contramov_credito(credito: Movimiento) -> Movimiento:
    return Movimiento.tomar(id=credito.id_contramov)


@pytest.fixture
def entrada_en_dolares(cuenta_en_dolares: CuentaInteractiva, dia: Dia, dolar: Moneda) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada en euros',
        importe=230,
        cta_entrada=cuenta_en_dolares,
        dia=dia,
        moneda=dolar,
    )


@pytest.fixture
def entrada_en_euros(cuenta_en_euros: CuentaInteractiva, dia: Dia, euro: Moneda) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada en euros',
        importe=230,
        cta_entrada=cuenta_en_euros,
        dia=dia,
        moneda=euro,
    )


@pytest.fixture
def mov_distintas_monedas(
        cuenta_con_saldo_en_dolares: CuentaInteractiva,
        cuenta_con_saldo_en_euros: CuentaInteractiva,
        dia: Dia,
        dolar: Moneda,
) -> Movimiento:
    return Movimiento.crear(
        concepto='Movimiento en distintas monedas',
        cta_entrada=cuenta_con_saldo_en_euros,
        cta_salida=cuenta_con_saldo_en_dolares,
        importe=10,
        dia=dia,
        moneda=dolar,
    )


@pytest.fixture
def conjunto_movimientos_varios_dias(cuenta, cuenta_2, cuenta_ajena, cuenta_ajena_2, request) -> QuerySet[Movimiento]:
    cuentas = list(CuentaInteractiva.todes())
    for x in range(1, 18):
        dia = Dia.crear(fecha=date(2022, 5, x))
        y = randint(0, len(cuentas)-1)
        movs_del_dia = randint(2, 5)
        for z in range(1, movs_del_dia):
            cta = cuentas[y]
            if x not in {5, 13}:
                mov = Movimiento(
                    concepto=f'Movimiento {x}',
                    importe=request.getfixturevalue('importe_aleatorio'),
                    dia=dia
                )
                if (y % 2) == 0:
                    mov.cta_entrada = cta
                else:
                    mov.cta_salida = cta
                mov.full_clean()
                mov.save()
    return Movimiento.todes()


