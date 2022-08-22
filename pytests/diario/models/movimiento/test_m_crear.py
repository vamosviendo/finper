from datetime import date
from unittest.mock import call

import pytest

from diario.models import Movimiento, Saldo
from utils import errors


@pytest.fixture
def mock_generar(mocker):
    return mocker.patch('diario.models.movimiento.Saldo.generar')


def test_no_admite_cuentas_acumulativas(cuenta_acumulativa):
    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=errors.CUENTA_ACUMULATIVA_EN_MOVIMIENTO):
        Movimiento.crear(
            'movimiento sobre acum', 100, cta_entrada=cuenta_acumulativa)


def test_guarda_fecha_de_hoy_por_defecto(cuenta):
    mov = Movimiento.crear(
        concepto='Cobranza en efectivo',
        importe=100,
        cta_entrada=cuenta
    )
    assert mov.fecha == date.today()


def test_mov_entrada_con_importe_negativo_se_crea_como_mov_salida(cuenta):
    mov = Movimiento.crear('Pago', -100, cta_entrada=cuenta)
    assert mov.cta_entrada is None
    assert mov.cta_salida == cuenta


def test_mov_salida_con_importe_negativo_se_crea_como_mov_entrada(cuenta):
    mov = Movimiento.crear('Pago', -100, cta_salida=cuenta)
    assert mov.cta_salida is None
    assert mov.cta_entrada == cuenta


def test_mov_traspaso_con_importe_negativo_intercambia_cta_entrada_y_salida(cuenta, cuenta_2):
    mov = Movimiento.crear(
        'Pago', -100, cta_entrada=cuenta_2, cta_salida=cuenta)
    assert mov.cta_salida == cuenta_2
    assert mov.cta_entrada == cuenta


def test_mov_con_importe_negativo_se_crea_con_importe_positivo(cuenta):
    mov = Movimiento.crear('Pago', -100, cta_entrada=cuenta)
    assert mov.importe == 100


def test_importe_cero_tira_error(cuenta):
    with pytest.raises(
            errors.ErrorImporteCero,
            match="Se intentó crear un movimiento con importe cero"
    ):
        Movimiento.crear('Pago', 0, cta_salida=cuenta)


def test_movimiento_se_guarda_como_no_automatico_por_defecto(cuenta):
    mov = Movimiento.crear('Pago', '200', cta_entrada=cuenta)
    assert not mov.es_automatico


def test_suma_importe_a_cta_entrada(cuenta, entrada):
    assert cuenta.saldo == entrada.importe


def test_resta_importe_de_cta_salida(cuenta, salida):
    assert cuenta.saldo == -salida.importe


def test_puede_traspasar_saldo_de_una_cuenta_a_otra(cuenta, cuenta_2):
    saldo_cuenta = cuenta.saldo
    saldo_cuenta_2 = cuenta_2.saldo

    mov = Movimiento.crear(
        concepto='Depósito',
        importe=60,
        cta_entrada=cuenta_2,
        cta_salida=cuenta
    )

    assert cuenta.saldo == saldo_cuenta - mov.importe
    assert cuenta_2.saldo == saldo_cuenta_2 + mov.importe


def test_mov_entrada_llama_a_generar_saldo_con_salida_False(mock_generar, cuenta):
    mov = Movimiento.crear('Nuevo mov', 20, cuenta)
    mock_generar.assert_called_once_with(mov, salida=False)


def test_mov_salida_llama_a_generar_saldo_con_salida_True(mock_generar, cuenta):
    mov = Movimiento.crear('Nuevo mov', 20, None, cuenta)
    mock_generar.assert_called_once_with(mov, salida=True)


def test_mov_traspaso_llama_a_generar_saldo_con_salida_false_para_cta_entrada_y_salida_True_para_cta_salida(
        mock_generar, cuenta, cuenta_2):
    mov = Movimiento.crear('Nuevo mov', 20, cuenta, cuenta_2)
    assert mock_generar.call_args_list == [call(mov, salida=False), call(mov, salida=True)]

def test_integrativo_genera_saldo_para_cta_entrada(cuenta):
    saldo_anterior_cuenta = cuenta.saldo
    mov = Movimiento.crear('Nuevo mov', 20, cuenta)

    saldo = Saldo.objects.get(cuenta=cuenta, movimiento=mov)
    assert saldo.cuenta.pk == cuenta.pk
    assert saldo.importe == saldo_anterior_cuenta + mov.importe
    assert saldo.movimiento == mov


def test_integrativo_genera_saldo_para_cta_salida(cuenta):
    saldo_anterior_cuenta = cuenta.saldo
    mov = Movimiento.crear('Nuevo mov', 20, None, cuenta)
    saldo = Saldo.objects.get(cuenta=cuenta, movimiento=mov)
    assert saldo.cuenta.pk == cuenta.pk
    assert saldo.importe == saldo_anterior_cuenta - mov.importe
    assert saldo.movimiento == mov


def test_integrativo_crear_movimiento_en_fecha_antigua_modifica_saldos_de_fechas_posteriores(
        cuenta, entrada, fecha_anterior):
    importe_saldo = Saldo.tomar(cuenta=cuenta, movimiento=entrada).importe
    mov_anterior = Movimiento.crear('Movimiento anterior', 30, cuenta, fecha=fecha_anterior)
    assert Saldo.tomar(cuenta=cuenta, movimiento=entrada).importe == importe_saldo + mov_anterior.importe

