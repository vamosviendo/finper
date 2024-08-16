from unittest.mock import ANY, MagicMock

import pytest

from diario.models import Saldo, Movimiento
from utils import errors
from utils.helpers_tests import signo


@pytest.fixture
def entrada_sin_saldo(entrada: Movimiento) -> Movimiento:
    Saldo.objects.get(cuenta=entrada.cta_entrada, movimiento=entrada).delete()
    return entrada


@pytest.fixture
def salida_sin_saldo(salida: Movimiento) -> Movimiento:
    Saldo.objects.get(cuenta=salida.cta_salida, movimiento=salida).delete()
    return salida


@pytest.fixture
def mock_crear(mocker) -> MagicMock:
    return mocker.patch('diario.models.Saldo.crear')


def test_crea_saldo_para_cuenta(entrada_sin_saldo, cuenta, mock_crear):
    Saldo.generar(entrada_sin_saldo, cuenta)
    mock_crear.assert_called_once_with(
        cuenta=cuenta,
        importe=entrada_sin_saldo.importe,
        movimiento=entrada_sin_saldo
    )


def test_con_salida_True_invierte_signo_importe(entrada_sin_saldo, cuenta, mock_crear):
    Saldo.generar(entrada_sin_saldo, cuenta, salida=True)
    mock_crear.assert_called_once_with(
        cuenta=ANY,
        movimiento=ANY,
        importe=-entrada_sin_saldo.importe
    )


def test_da_error_si_cuenta_no_pertenece_a_movimiento(entrada_sin_saldo, cuenta_2):
    with pytest.raises(
        errors.ErrorCuentaNoFiguraEnMovimiento,
        match='La cuenta "cuenta 2" no pertenece al movimiento "Entrada"'
    ):
        Saldo.generar(entrada_sin_saldo, cuenta_2)


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_no_recibe_cuenta_y_salida_False_toma_cta_entrada_del_movimiento_como_cuenta(
        sentido, request):
    mov = request.getfixturevalue(f'{sentido}_sin_saldo')
    es_entrada = sentido == 'entrada'
    mock_crear = request.getfixturevalue('mock_crear')
    Saldo.generar(mov, salida=not es_entrada)
    mock_crear.assert_called_once_with(
        movimiento=ANY,
        importe=ANY,
        cuenta=getattr(mov, f'cta_{sentido}')
    )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_importe_de_saldo_creado_es_igual_a_suma_del_importe_del_movimiento_y_el_ultimo_saldo_anterior_de_la_cuenta(
        entrada_anterior, sentido, cuenta, request):
    importe_saldo_anterior = Saldo.objects.get(cuenta=cuenta, movimiento=entrada_anterior).importe
    mov = request.getfixturevalue(f'{sentido}_sin_saldo')
    es_entrada = sentido == 'entrada'
    s = signo(es_entrada)
    mock_crear = request.getfixturevalue('mock_crear')
    Saldo.generar(mov, cuenta, salida=not es_entrada)
    mock_crear.assert_called_once_with(
        cuenta=ANY,
        movimiento=ANY,
        importe=importe_saldo_anterior + s*mov.importe
    )


def test_si_moneda_del_movimiento_es_distinta_de_la_de_la_cuenta_suma_importe_del_movimiento_ajustado_segun_cotizacion_del_mismo(
        mov_distintas_monedas, cuenta_con_saldo_en_euros, mock_crear):
    Saldo.objects.get(cuenta=cuenta_con_saldo_en_euros, movimiento=mov_distintas_monedas).delete()
    saldo_anterior = Saldo.objects.filter(cuenta=cuenta_con_saldo_en_euros).last().importe
    Saldo.generar(mov_distintas_monedas, cuenta_con_saldo_en_euros)
    print('saldo anterior:', saldo_anterior)
    mock_crear.assert_called_once_with(
        cuenta=cuenta_con_saldo_en_euros,
        movimiento=mov_distintas_monedas,
        importe=saldo_anterior + mov_distintas_monedas.importe * mov_distintas_monedas.cotizacion
    )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_importe_de_saldo_creado_no_suma_importe_de_saldo_correspondiente_a_movimiento_posterior_preexistente(
        salida_posterior, sentido, cuenta, request):
    mov = request.getfixturevalue(f'{sentido}_sin_saldo')
    es_entrada = sentido == 'entrada'
    s = signo(es_entrada)
    mock_crear = request.getfixturevalue('mock_crear')
    Saldo.generar(mov, cuenta, salida=not es_entrada)

    mock_crear.assert_called_once_with(
        cuenta=ANY,
        movimiento=ANY,
        importe=s*mov.importe
    )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_actualiza_saldos_posteriores_con_importe_de_movimiento(
        mocker, sentido, cuenta, request):
    mov = request.getfixturevalue(f'{sentido}_sin_saldo')
    es_entrada = sentido == 'entrada'
    s = signo(es_entrada)
    mock_actualizar_posteriores = mocker.patch(
        'diario.models.Saldo._actualizar_posteriores',
        autospec=True
    )
    saldo = Saldo.generar(mov, cuenta, salida=not es_entrada)
    mock_actualizar_posteriores.assert_called_once_with(saldo, s*mov.importe)


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_integrativo_actualiza_saldos_posteriores(
        sentido, cuenta, salida_posterior, request):
    mov = request.getfixturevalue(f'{sentido}_sin_saldo')
    es_entrada = sentido == 'entrada'
    s = signo(es_entrada)
    saldo_posterior = Saldo.tomar(cuenta=cuenta, movimiento=salida_posterior).importe

    Saldo.generar(mov, cuenta, salida=not es_entrada)
    assert \
        Saldo.tomar(cuenta=cuenta, movimiento=salida_posterior).importe == \
        saldo_posterior + s*mov.importe


def test_devuelve_saldo_generado(entrada_sin_saldo, cuenta):
    assert \
        Saldo.generar(entrada_sin_saldo, cuenta) == \
        Saldo.objects.get(cuenta=cuenta, movimiento=entrada_sin_saldo)
