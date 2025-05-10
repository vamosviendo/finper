from unittest.mock import ANY, MagicMock

import pytest

from diario.models import Saldo, Movimiento, SaldoDiario, Dia
from utils.helpers_tests import signo
from utils.varios import el_que_no_es


@pytest.fixture
def entrada_sin_saldo_diario(entrada: Movimiento) -> Movimiento:
    SaldoDiario.objects.get(cuenta=entrada.cta_entrada, dia=entrada.dia).delete()
    return entrada


@pytest.fixture
def salida_sin_saldo_diario(salida: Movimiento) -> Movimiento:
    SaldoDiario.objects.get(cuenta=salida.cta_salida, dia=salida.dia).delete()
    return salida


@pytest.fixture
def traspaso_sin_saldos_diarios(traspaso: Movimiento) -> Movimiento:
    for cta in (traspaso.cta_entrada, traspaso.cta_salida):
        SaldoDiario.objects.get(cuenta=cta, dia=traspaso.dia).delete()
        return traspaso


@pytest.fixture
def mock_saldo_crear(mocker) -> MagicMock:
    return mocker.patch('diario.models.SaldoDiario.crear')


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_crea_saldo_para_cuenta_indicada_en_sentido(sentido, request):
    mov = request.getfixturevalue(f"{sentido}_sin_saldo_diario")
    mock_saldo_crear = request.getfixturevalue("mock_saldo_crear")
    importe = signo(sentido == "entrada") * mov.importe
    SaldoDiario.calcular(mov, sentido)
    mock_saldo_crear.assert_called_once_with(
        cuenta=getattr(mov, f"cta_{sentido}"),
        importe=importe,
        dia=mov.dia,
    )


def test_da_error_si_sentido_no_es_entrada_o_salida(entrada_sin_saldo_diario):
    with pytest.raises(
        ValueError,
        match='Los valores aceptados para arg "sentido" son "entrada", "cta_entrada", "salida", "cta_salida"'
    ):
        SaldoDiario.calcular(entrada_sin_saldo_diario, "pastafrola")


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_acepta_cta_entrada_o_cta_salida_para_arg_sentido(sentido, request):
    mov = request.getfixturevalue(f"{sentido}_sin_saldo_diario")
    try:
        SaldoDiario.calcular(mov, f"cta_{sentido}")
    except ValueError:
        raise AssertionError(f"No permite cta_{sentido} como valor de arg 'sentido'")


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_no_recibe_sentido_y_no_es_movimiento_de_traspaso_toma_cuenta_del_movimiento(sentido, request):
    mov = request.getfixturevalue(f'{sentido}_sin_saldo_diario')
    mock_saldo_crear = request.getfixturevalue('mock_saldo_crear')
    SaldoDiario.calcular(mov)
    mock_saldo_crear.assert_called_once_with(
        dia=ANY,
        importe=getattr(mov, f"importe_cta_{sentido}"),
        cuenta=getattr(mov, f"cta_{sentido}")
    )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_no_recibe_sentido_y_es_movimiento_de_traspaso_da_typeerror(sentido, traspaso_sin_saldos_diarios):
    with pytest.raises(ValueError, match='En un movimiento de traspaso debe especificarse argumento "sentido"'):
        SaldoDiario.calcular(traspaso_sin_saldos_diarios)


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_importe_de_saldo_diario_creado_es_igual_a_importe_de_saldo_diario_anterior_mas_menos_importe_del_movimiento(
        saldo_diario_anterior, sentido, request):
    mov = request.getfixturevalue(f"{sentido}_sin_saldo_diario")
    cuenta = getattr(mov, f"cta_{sentido}")
    importe_mov = getattr(mov, f"importe_cta_{sentido}")
    SaldoDiario.calcular(mov)
    saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
    assert saldo_diario.importe == saldo_diario_anterior.importe + importe_mov


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_si_ya_existe_saldo_del_dia_del_movimiento_suma_o_resta_a_su_importe_el_importe_del_movimiento(
        sentido, request):
    mov = request.getfixturevalue(sentido)
    saldo_diario = request.getfixturevalue("saldo_diario")
    importe_saldo_diario = saldo_diario.importe
    importe_mov = getattr(mov, f"importe_cta_{sentido}")

    SaldoDiario.calcular(mov, sentido)

    assert saldo_diario.tomar_de_bd().importe == importe_saldo_diario + importe_mov


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_moneda_del_movimiento_es_distinta_de_la_de_la_cuenta_suma_importe_del_movimiento_ajustado_segun_cotizacion_del_mismo(
        sentido, request):
    mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
    cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_opuesto}")
    dia = mov_distintas_monedas.dia
    dia_anterior = dia.timedelta(-1)
    saldo_diario_anterior = SaldoDiario.crear(cuenta=cuenta, dia=dia_anterior, importe=3)
    mock_saldo_crear = request.getfixturevalue('mock_saldo_crear')
    SaldoDiario.objects.get(cuenta=cuenta, dia=dia).delete()

    SaldoDiario.calcular(mov_distintas_monedas, sentido_opuesto)

    mock_saldo_crear.assert_called_once_with(
        cuenta=cuenta,
        dia=dia,
        importe=saldo_diario_anterior.importe + getattr(mov_distintas_monedas, f"importe_cta_{sentido_opuesto}")
    )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_importe_de_saldo_diario_creado_no_suma_importe_de_saldo_correspondiente_a_dia_posterior_preexistente(
        saldo_diario_posterior, sentido, cuenta, request):
    mov = request.getfixturevalue(f'{sentido}_sin_saldo_diario')
    es_entrada = sentido == 'entrada'
    s = signo(es_entrada)
    mock_crear = request.getfixturevalue('mock_saldo_crear')
    SaldoDiario.calcular(mov, sentido)

    mock_crear.assert_called_once_with(
        cuenta=ANY,
        dia=ANY,
        importe=s*mov.importe
    )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_integrativo_actualiza_saldos_posteriores(
        sentido, cuenta, saldo_diario_posterior, request):
    importe_saldo_posterior = saldo_diario_posterior.importe

    mov = request.getfixturevalue(sentido)

    saldo_diario_posterior.refresh_from_db()
    assert \
        saldo_diario_posterior.importe == \
        importe_saldo_posterior + getattr(mov, f"importe_cta_{sentido}")


def test_devuelve_saldo_diario_calculado(entrada_sin_saldo_diario, cuenta):
    assert \
        SaldoDiario.calcular(entrada_sin_saldo_diario) == \
        SaldoDiario.objects.get(cuenta=cuenta, dia=entrada_sin_saldo_diario.dia)


def test_devuelve_saldo_diario_modificado(entrada, cuenta, request):
    saldo_diario = SaldoDiario.tomar(cuenta=entrada.cta_entrada, dia=entrada.dia)
    saldo_diario.importe -= entrada.importe
    saldo_diario.clean_save()
    importe_saldo_diario = saldo_diario.importe

    valor_devuelto = SaldoDiario.calcular(entrada)

    assert valor_devuelto == saldo_diario
    assert valor_devuelto.importe == importe_saldo_diario + entrada.importe
