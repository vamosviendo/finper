from unittest.mock import ANY, MagicMock

import pytest

from diario.models import Saldo, Movimiento
from utils.helpers_tests import signo
from utils.varios import el_que_no_es


@pytest.fixture
def entrada_sin_saldo(entrada: Movimiento) -> Movimiento:
    Saldo.objects.get(cuenta=entrada.cta_entrada, movimiento=entrada).delete()
    return entrada


@pytest.fixture
def salida_sin_saldo(salida: Movimiento) -> Movimiento:
    Saldo.objects.get(cuenta=salida.cta_salida, movimiento=salida).delete()
    return salida


@pytest.fixture
def traspaso_sin_saldos(traspaso: Movimiento) -> Movimiento:
    for cta in (traspaso.cta_entrada, traspaso.cta_salida):
        Saldo.objects.get(cuenta=cta, movimiento=traspaso).delete()
        return traspaso


@pytest.fixture
def mock_saldo_crear(mocker) -> MagicMock:
    return mocker.patch('diario.models.Saldo.crear')


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_crea_saldo_para_cuenta_indicada_en_sentido(sentido, request):
    mov = request.getfixturevalue(f"{sentido}_sin_saldo")
    mock_saldo_crear = request.getfixturevalue("mock_saldo_crear")
    importe = signo(sentido == "entrada") * mov.importe
    Saldo.generar(mov, sentido)
    mock_saldo_crear.assert_called_once_with(
        cuenta=getattr(mov, f"cta_{sentido}"),
        importe=importe,
        movimiento=mov,
    )


def test_da_error_si_sentido_no_es_entrada_o_salida(entrada_sin_saldo):
    with pytest.raises(
        ValueError,
        match='Los valores aceptados para arg "sentido" son "entrada", "cta_entrada", "salida", "cta_salida"'
    ):
        Saldo.generar(entrada_sin_saldo, "pastafrola")


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_acepta_cta_entrada_o_cta_salida_para_arg_sentido(sentido, request):
    mov = request.getfixturevalue(f"{sentido}_sin_saldo")
    try:
        Saldo.generar(mov, f"cta_{sentido}")
    except ValueError:
        raise AssertionError(f"No permite cta_{sentido} como valor de arg 'sentido'")


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_no_recibe_sentido_y_no_es_movimiento_de_traspaso_toma_cuenta_del_movimiento(sentido, request):
    mov = request.getfixturevalue(f'{sentido}_sin_saldo')
    mock_saldo_crear = request.getfixturevalue('mock_saldo_crear')
    Saldo.generar(mov)
    mock_saldo_crear.assert_called_once_with(
        movimiento=ANY,
        importe=getattr(mov, f"importe_cta_{sentido}"),
        cuenta=getattr(mov, f"cta_{sentido}")
    )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_no_recibe_sentido_y_es_movimiento_de_traspaso_da_typeerror(sentido, traspaso_sin_saldos, request):
    with pytest.raises(TypeError, match='En un movimiento de traspaso debe especificarse argumento "sentido"'):
        Saldo.generar(traspaso_sin_saldos)


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_importe_de_saldo_creado_es_igual_a_suma_del_importe_del_movimiento_y_el_ultimo_saldo_anterior_de_la_cuenta(
        entrada_anterior, sentido, cuenta, request):
    importe_saldo_anterior = Saldo.objects.get(cuenta=cuenta, movimiento=entrada_anterior).importe
    mov = request.getfixturevalue(f'{sentido}_sin_saldo')
    mock_saldo_crear = request.getfixturevalue('mock_saldo_crear')

    Saldo.generar(mov, sentido)

    mock_saldo_crear.assert_called_once_with(
        cuenta=ANY,
        movimiento=ANY,
        importe=importe_saldo_anterior + getattr(mov, f"importe_cta_{sentido}")
    )


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_moneda_del_movimiento_es_distinta_de_la_de_la_cuenta_suma_importe_del_movimiento_ajustado_segun_cotizacion_del_mismo(
        sentido, cuenta_con_saldo_en_euros, request):
    mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
    cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_opuesto}")
    mock_saldo_crear = request.getfixturevalue('mock_saldo_crear')

    Saldo.objects.get(cuenta=cuenta, movimiento=mov_distintas_monedas).delete()
    saldo_anterior = Saldo.objects.filter(cuenta=cuenta).last().importe
    Saldo.generar(mov_distintas_monedas, sentido_opuesto)

    mock_saldo_crear.assert_called_once_with(
        cuenta=cuenta,
        movimiento=mov_distintas_monedas,
        importe=saldo_anterior + getattr(mov_distintas_monedas, f"importe_cta_{sentido_opuesto}")
    )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_importe_de_saldo_creado_no_suma_importe_de_saldo_correspondiente_a_movimiento_posterior_preexistente(
        salida_posterior, sentido, cuenta, request):
    mov = request.getfixturevalue(f'{sentido}_sin_saldo')
    es_entrada = sentido == 'entrada'
    s = signo(es_entrada)
    mock_crear = request.getfixturevalue('mock_saldo_crear')
    Saldo.generar(mov, sentido)

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
    saldo = Saldo.generar(mov, sentido)
    mock_actualizar_posteriores.assert_called_once_with(saldo, s*mov.importe)


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_integrativo_actualiza_saldos_posteriores(
        sentido, cuenta, salida_posterior, request):
    mov = request.getfixturevalue(f'{sentido}_sin_saldo')
    es_entrada = sentido == 'entrada'
    s = signo(es_entrada)
    saldo_posterior = Saldo.tomar(cuenta=cuenta, movimiento=salida_posterior).importe

    Saldo.generar(mov, sentido)
    assert \
        Saldo.tomar(cuenta=cuenta, movimiento=salida_posterior).importe == \
        saldo_posterior + s*mov.importe


def test_devuelve_saldo_generado(entrada_sin_saldo, cuenta):
    assert \
        Saldo.generar(entrada_sin_saldo) == \
        Saldo.objects.get(cuenta=cuenta, movimiento=entrada_sin_saldo)
