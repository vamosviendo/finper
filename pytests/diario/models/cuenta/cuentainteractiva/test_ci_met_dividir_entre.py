import re
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError

from diario.models import Cuenta, Movimiento
from utils.errors import ErrorFechaCreacionPosteriorAConversion, \
    ErrorMovimientoPosteriorAConversion, ErrorDeSuma


@pytest.fixture
def mock_saldo_ok(mocker) -> MagicMock:
    return mocker.patch('diario.models.cuenta.CuentaInteractiva.saldo_ok')


def test_verifica_saldo_cuenta_antes_de_dividirla(mock_saldo_ok, cuenta, dicts_subcuentas):
    cuenta.dividir_entre(*dicts_subcuentas)
    mock_saldo_ok.assert_called_once()


def test_da_error_si_saldo_no_ok(mock_saldo_ok, cuenta, dicts_subcuentas):
    mock_saldo_ok.return_value = False
    with pytest.raises(
            ValidationError,
            match=re.escape(
                f'Saldo de cuenta "{cuenta.nombre}" no coincide '
                f'con sus movimientos. Saldo: {cuenta.saldo()} - '
                f'Total movimientos: {cuenta.total_movs()}'
            )
    ):
        cuenta.dividir_entre(*dicts_subcuentas)


def test_genera_cuentas_a_partir_de_lista_de_diccionarios(cuenta, dicts_subcuentas):
    cuenta.dividir_entre(*dicts_subcuentas)

    subcuenta1 = Cuenta.tomar(sk='sc1')
    subcuenta2 = Cuenta.tomar(sk='sc2')
    assert subcuenta1.nombre == "subcuenta 1"
    assert subcuenta2.nombre == "subcuenta 2"


def test_devuelve_lista_con_subcuentas_creadas(cuenta, dicts_subcuentas):
    assert \
        cuenta.dividir_entre(*dicts_subcuentas) == \
        [Cuenta.tomar(sk='sc1'), Cuenta.tomar(sk='sc2')]


def test_cuentas_generadas_son_subcuentas_de_cuenta_madre(cuenta, dicts_subcuentas):
    cuenta.dividir_entre(*dicts_subcuentas)
    cta_madre = cuenta.tomar_del_sk()
    cta1 = Cuenta.tomar(sk='sc1')
    cta2 = Cuenta.tomar(sk='sc2')

    assert cta1.cta_madre == cta_madre
    assert cta2.cta_madre == cta_madre
    assert list(cta_madre.subcuentas.all()) == [cta1, cta2]


def test_cuentas_generadas_toman_fecha_de_creacion_de_argumento_fecha(cuenta, dicts_subcuentas, fecha_posterior):
    cta1, cta2 = cuenta.dividir_entre(
        *dicts_subcuentas,
        fecha=fecha_posterior
    )
    assert cta1.fecha_creacion == fecha_posterior
    assert cta2.fecha_creacion == fecha_posterior


def test_titular_de_cuenta_madre_es_por_defecto_el_titular_de_cuentas_generadas(cuenta, dicts_subcuentas):
    cta1, cta2 = cuenta.dividir_entre(*dicts_subcuentas)
    assert cta1.titular == cuenta.titular
    assert cta2.titular == cuenta.titular


def test_permite_asignar_otros_titulares_a_cuentas_generadas(cuenta, dicts_subcuentas, otro_titular):
    dicts_subcuentas[1].update({'titular': otro_titular})

    _, cta2 = cuenta.dividir_entre(dicts_subcuentas)

    assert cta2.titular == otro_titular


def test_si_recibe_titular_none_usa_titular_por_defecto(cuenta, dicts_subcuentas):
    for dic in dicts_subcuentas:
        dic.update({'titular': None})

    sc1, _ = cuenta.dividir_entre(*dicts_subcuentas)
    assert sc1.titular == cuenta.titular


def test_convierte_titular_en_titular_original(cuenta, dicts_subcuentas, otro_titular):
    titular = cuenta.titular
    for dict in dicts_subcuentas:
        dict.update({'titular': otro_titular})

    ca = cuenta.dividir_y_actualizar(dicts_subcuentas)
    assert ca.titular_original == titular


def test_genera_movimientos_de_salida_en_cta_madre_con_saldo_positivo(cuenta_con_saldo, dicts_subcuentas):
    movs_cuenta_antes = cuenta_con_saldo.movs_directos().count()
    importe1 = dicts_subcuentas[0]['saldo']
    importe2 = cuenta_con_saldo.saldo() - importe1

    cuenta_con_saldo.dividir_entre(*dicts_subcuentas)
    cuenta = Cuenta.tomar(sk=cuenta_con_saldo.sk, polymorphic=False)

    assert cuenta.movs_directos().count() == movs_cuenta_antes + 2

    mov1 = list(cuenta.movs_directos())[-2]
    mov2 = list(cuenta.movs_directos())[-1]

    assert mov1.concepto == "Traspaso de saldo"
    assert mov1.importe == abs(importe1)
    assert mov1.cta_salida == cuenta

    assert mov2.concepto == "Traspaso de saldo"
    assert mov2.importe == abs(importe2)
    assert mov2.cta_salida == cuenta


def test_genera_movimientos_de_entrada_en_cta_madre_con_saldo_negativo(
        cuenta_con_saldo_negativo, dicts_subcuentas):
    movs_cuenta_antes = cuenta_con_saldo_negativo.movs_directos().count()
    importe1 = dicts_subcuentas[0]['saldo'] = -50
    importe2 = cuenta_con_saldo_negativo.saldo() - importe1

    cuenta_con_saldo_negativo.dividir_entre(*dicts_subcuentas)
    cuenta = Cuenta.tomar(sk=cuenta_con_saldo_negativo.sk, polymorphic=False)

    assert cuenta.movs_directos().count() == movs_cuenta_antes + 2

    mov1 = list(cuenta.movs_directos())[-2]
    mov2 = list(cuenta.movs_directos())[-1]

    assert mov1.concepto == "Traspaso de saldo"
    assert mov1.importe == abs(importe1)
    assert mov1.cta_entrada == cuenta

    assert mov2.concepto == "Traspaso de saldo"
    assert mov2.importe == abs(importe2)
    assert mov2.cta_entrada == cuenta


def test_agrega_subcuenta_como_contrapartida_de_cuenta_en_movimiento(
        cuenta_con_saldo, dicts_subcuentas):
    cuenta_con_saldo = cuenta_con_saldo.dividir_y_actualizar(*dicts_subcuentas)

    movs = list(cuenta_con_saldo.movs_directos())[-2:]

    for i, mov in enumerate(movs):
        assert \
            mov.cta_entrada.como_subclase() == \
            Cuenta.tomar(sk=dicts_subcuentas[i]['sk'])


def test_acepta_mas_de_dos_subcuentas(cuenta, dicts_subcuentas):
    dicts_subcuentas[1]['saldo'] = 130
    dicts_subcuentas.append(
        {'nombre': 'subcuenta 3', 'sk': 'sc3'})

    cuenta = cuenta.dividir_y_actualizar(*dicts_subcuentas)

    assert cuenta.subcuentas.count() == 3
    assert sum([c.saldo() for c in cuenta.subcuentas.all()]) == cuenta.saldo()


def test_cuenta_se_convierte_en_acumulativa(cuenta, dicts_subcuentas):
    pk = cuenta.pk
    cuenta.dividir_entre(dicts_subcuentas)
    cuenta = Cuenta.tomar(pk=pk)

    assert cuenta.es_acumulativa


def test_guarda_fecha_conversion(cuenta):
    fecha = date.today()
    cta_acum = cuenta.dividir_y_actualizar(
        ['subi1', 'si1', 0], ['subi2', 'si2']
    )
    assert cta_acum.fecha_conversion == fecha


def test_acepta_fecha_de_conversion_distinta_de_la_actual(cuenta, dicts_subcuentas, fecha_posterior):
    cta_acum = cuenta.dividir_y_actualizar(
        *dicts_subcuentas, fecha=fecha_posterior)
    assert cta_acum.fecha_conversion == fecha_posterior


def test_movimientos_de_traspaso_de_saldo_tienen_fecha_igual_a_la_de_conversion(
        cuenta, dicts_subcuentas, fecha_posterior):
    cuenta = cuenta.dividir_y_actualizar(
        *dicts_subcuentas,
        fecha=fecha_posterior
    )
    assert list(cuenta.movs_directos())[-2].fecha == fecha_posterior
    assert list(cuenta.movs_directos())[-1].fecha == fecha_posterior


def test_no_acepta_fecha_de_conversion_anterior_a_fecha_de_creacion_de_la_cuenta(
        cuenta, titular, dicts_subcuentas_sin_saldo):
    titular.fecha_alta -= timedelta(2)
    titular.save()

    with pytest.raises(ErrorFechaCreacionPosteriorAConversion):
        cuenta.dividir_entre(
            *dicts_subcuentas_sin_saldo,
            fecha=cuenta.fecha_creacion - timedelta(1)
        )


def test_no_acepta_fecha_de_conversion_anterior_a_la_de_cualquier_movimiento_de_la_cuenta(
        cuenta, dicts_subcuentas, salida_posterior, entrada_tardia):
    with pytest.raises(ErrorMovimientoPosteriorAConversion):
        cuenta.dividir_entre(
            *dicts_subcuentas,
            fecha=entrada_tardia.fecha - timedelta(1)
        )


def test_calcula_saldo_de_hasta_una_subcuenta_sin_saldo(cuenta, dicts_subcuentas):
    dicts_subcuentas[1]['saldo'] = 130
    dicts_subcuentas.append({'nombre': 'Subcuenta 3', 'sk': 'sc3'})

    sc1, sc2, sc3 = cuenta.dividir_entre(*dicts_subcuentas)

    assert sc3.saldo() == -180


def test_no_acepta_mas_de_una_subcuenta_sin_saldo(cuenta, dicts_subcuentas):
    dicts_subcuentas.append({'nombre': 'Subcuenta 3', 'sk': 'sc3'})
    with pytest.raises(ErrorDeSuma):
        cuenta.dividir_entre(*dicts_subcuentas)


def test_da_error_si_suma_de_saldos_subcuentas_no_coinciden_con_saldo(cuenta_con_saldo, dicts_subcuentas):
    dicts_subcuentas[1]['saldo'] = 239

    with pytest.raises(
            ErrorDeSuma,
            match="Suma errónea. Saldos de subcuentas deben sumar 100.00"):
        cuenta_con_saldo.dividir_entre(*dicts_subcuentas)


def test_cuenta_convertida_conserva_movimientos_anteriores(
        cuenta, entrada, salida_posterior, dicts_subcuentas):
    cta_acum = cuenta.dividir_y_actualizar(*dicts_subcuentas)
    assert cta_acum.cantidad_movs() == 4
    assert cta_acum.movs_directos()[0] == entrada
    assert cta_acum.movs_directos()[1] == salida_posterior


def test_cuenta_convertida_conserva_nombre(cuenta, dicts_subcuentas):
    nombre_cuenta = cuenta.nombre
    cta_acum = cuenta.dividir_y_actualizar(*dicts_subcuentas)
    assert cta_acum.nombre == nombre_cuenta


def test_guarda_datos_de_cuentas_involucradas_en_detalle_del_movimiento(cuenta, dicts_subcuentas):
    sc1, sc2 = cuenta.dividir_entre(*dicts_subcuentas)
    mov1, mov2 = [sc.movs().first() for sc in (sc1, sc2)]

    assert mov1.concepto == "Traspaso de saldo"
    assert mov1.detalle == \
           f"Saldo pasado por {cuenta.nombre.capitalize()} " \
           f"a nueva subcuenta {dicts_subcuentas[0]['nombre']}"
    assert mov2.concepto == "Traspaso de saldo"
    assert mov2.detalle == \
           f"Saldo pasado por {cuenta.nombre.capitalize()} " \
           f"a nueva subcuenta {dicts_subcuentas[1]['nombre']}"


def test_marca_movimientos_de_traspaso_de_saldos_como_convierte_cuenta(cuenta, dicts_subcuentas):
    sc1, sc2 = cuenta.dividir_entre(*dicts_subcuentas)
    mov1, mov2 = [sc.movs().first() for sc in (sc1, sc2)]

    assert mov1.convierte_cuenta
    assert mov2.convierte_cuenta


def test_subcuentas_toman_moneda_de_cuenta_madre(cuenta_en_dolares, dicts_subcuentas, dolar):
    sc1, sc2 = cuenta_en_dolares.dividir_entre(*dicts_subcuentas)
    assert sc1.moneda == dolar
    assert sc2.moneda == dolar


def test_si_traspasa_saldo_a_cuenta_de_otro_titular_genera_contramovimiento_de_credito(
        cuenta, dicts_subcuentas_otro_titular):
    _, scot = cuenta.dividir_entre(*dicts_subcuentas_otro_titular)
    traspaso = scot.movs().first()
    assert traspaso.id_contramov is not None
    contramov = Movimiento.tomar(pk=traspaso.id_contramov)
    assert contramov.importe == traspaso.importe


def test_si_traspasa_saldo_a_cuenta_de_otro_titular_con_esgratis_True_no_genera_contramovimiento_de_credito(
        cuenta, dicts_division_gratuita):
    _, scot = cuenta.dividir_entre(*dicts_division_gratuita)
    traspaso = scot.movs().first()
    assert traspaso.id_contramov is None
