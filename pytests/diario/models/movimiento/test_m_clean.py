from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError

from diario.models import Movimiento, Cuenta
from utils import errors
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_requiere_al_menos_una_cuenta(fecha):
    mov = Movimiento(
        fecha=fecha,
        concepto='Movimiento sin cuentas',
        importe=100
    )
    with pytest.raises(ValidationError, match=errors.CUENTA_INEXISTENTE):
        mov.full_clean()


def test_no_admite_misma_cuenta_de_entrada_y_de_salida(cuenta, fecha):
    mov = Movimiento(
        fecha=fecha,
        concepto='Movimiento con cuentas iguales',
        importe=100,
        cta_entrada=cuenta,
        cta_salida=cuenta
    )
    with pytest.raises(ValidationError, match=errors.CUENTAS_IGUALES):
        mov.full_clean()


def test_permite_movimientos_duplicados(fecha, cuenta):
    Movimiento.crear(
        fecha=fecha,
        concepto='Movimiento igual a otro',
        importe=100,
        cta_entrada=cuenta
    )
    mov = Movimiento(
        fecha=fecha,
        concepto='Movimiento igual a otro',
        importe=100,
        cta_entrada=cuenta
    )
    mov.full_clean()    # No debe dar error


def test_movimiento_no_automatico_no_admite_cuenta_credito(
        cuenta_credito_acreedor, cuenta_credito_deudor):
    mov_no_e = Movimiento(
        concepto='Movimiento con cta_entrada crédito',
        importe=50,
        cta_entrada=cuenta_credito_deudor,
    )
    mov_no_s = Movimiento(
        concepto='Movimiento con cta_salida crédito',
        importe=50,
        cta_salida=cuenta_credito_acreedor
    )
    with pytest.raises(
        ValidationError,
        match='No se permite cuenta crédito en movimiento de entrada o salida'
    ):
        mov_no_e.full_clean()
    with pytest.raises(
        ValidationError,
        match='No se permite cuenta crédito en movimiento de entrada o salida'
    ):
        mov_no_s.full_clean()


def test_cuenta_credito_no_puede_ser_cta_entrada_contra_cta_salida_normal(
        cuenta, cuenta_credito_deudor):
    mov_no = Movimiento(
        concepto='Movimiento entre cuentas incompatibles',
        importe=50,
        cta_entrada=cuenta_credito_deudor,
        cta_salida=cuenta
    )

    with pytest.raises(
        ValidationError,
        match='No se permite traspaso entre cuenta crédito y cuenta normal'
    ):
        mov_no.full_clean()


def test_cuenta_credito_no_puede_ser_cta_salida_contra_cta_entrada_normal(
        cuenta, cuenta_credito_acreedor):
    mov_no = Movimiento(
        concepto='Movimiento entre cuentas incompatibles',
        importe=50,
        cta_entrada=cuenta,
        cta_salida=cuenta_credito_acreedor
    )

    with pytest.raises(
            ValidationError,
            match='No se permite traspaso entre cuenta crédito y cuenta normal'
    ):
        mov_no.full_clean()


def test_cuenta_credito_solo_puede_moverse_contra_su_contracuenta(
        cuenta_credito_acreedor, cuenta_ajena, titular_gordo):
    # cc12, cc21 = self.generar_cuentas_credito()
    # titular3 = Titular.crear(nombre='Titular 3', titname='tit3')
    cuenta_gorda = Cuenta.crear(
        nombre='Cuenta titular gordo', slug='ctg', titular=titular_gordo)
    mov = Movimiento.crear(
        'Otro préstamo', 70, cuenta_ajena, cuenta_gorda)
    # cc32, cc23 = movimiento2.recuperar_cuentas_credito()
    ca_gordo_otro, _ = mov.recuperar_cuentas_credito()
    mov_no = Movimiento(
        concepto='Movimiento entre cuentas incompatibles',
        importe=50,
        cta_entrada=cuenta_credito_acreedor,
        cta_salida=ca_gordo_otro
    )

    with pytest.raises(
        ValidationError,
        match='"préstamo entre gordo y otro" no es la contrapartida '
        'de "préstamo entre otro y titular"'
    ):
        mov_no.full_clean()


def test_no_se_permite_modificar_movimiento_automatico(credito):
    contramov = Movimiento.tomar(id=credito.id_contramov)
    contramov.concepto = 'otro concepto'
    with pytest.raises(
            ValidationError,
            match="No se puede modificar movimiento automático"
    ):
        contramov.full_clean()


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_no_puede_modificarse_importe_cuenta_acumulativa(
        sentido, importe_alto, request):
    mov = request.getfixturevalue(f'{sentido}_con_ca')

    mov.importe = importe_alto
    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
        mov.full_clean()


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_no_puede_modificarse_importe_de_mov_de_traspaso_con_una_cuenta_acumulativa(
        sentido, importe_alto, request):
    traspaso = request.getfixturevalue(f'traspaso_con_cta_{sentido}_a')

    traspaso.importe = importe_alto
    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
        traspaso.full_clean()


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_no_puede_reemplazarse_cuenta_si_es_acumulativa(sentido, cuenta_2, request):
    mov = request.getfixturevalue(f'{sentido}_con_ca')

    setattr(mov, f'cta_{sentido}', cuenta_2)
    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=errors.CUENTA_ACUMULATIVA_RETIRADA):
        mov.full_clean()


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_no_puede_retirarse_cuenta_de_traspaso_si_es_acumulativa(sentido, traspaso):
    cuenta = getattr(traspaso, f'cta_{sentido}')
    dividir_en_dos_subcuentas(cuenta)

    setattr(traspaso, f'cta_{sentido}', None)
    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=errors.CUENTA_ACUMULATIVA_RETIRADA):
        traspaso.full_clean()


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_no_puede_agregarse_cuenta_acumulativa(sentido, cuenta_acumulativa, request):
    mov = request.getfixturevalue(sentido)
    contrasentido = 'salida' if sentido == 'entrada' else 'entrada'

    setattr(mov, f'cta_{contrasentido}', cuenta_acumulativa)

    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=errors.CUENTA_ACUMULATIVA_AGREGADA):
        mov.full_clean()


def test_no_permite_fecha_anterior_a_creacion_de_cuenta(fecha, fecha_anterior):
    cuenta = Cuenta.crear('Cuenta', 'cta', fecha_creacion=fecha)
    entrada = Movimiento(concepto='Entrada', importe=10, cta_entrada=cuenta, fecha=fecha_anterior)
    salida = Movimiento(concepto='Salida', importe=20, cta_salida=cuenta, fecha=fecha_anterior)
    with pytest.raises(
        errors.ErrorMovimientoAnteriorAFechaCreacion,
        match='Movimiento anterior a la fecha de creación de la cuenta'
    ):
        entrada.clean()
    with pytest.raises(
        errors.ErrorMovimientoAnteriorAFechaCreacion,
        match='Movimiento anterior a la fecha de creación de la cuenta'
    ):
        salida.clean()


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_no_puede_asignarse_fecha_posterior_a_conversion_en_mov_con_cuenta_acumulativa(
        sentido, fecha_posterior, request):
    mov = request.getfixturevalue(sentido)
    cuenta = getattr(mov, f'cta_{sentido}')
    cuenta = dividir_en_dos_subcuentas(cuenta, fecha=fecha_posterior)
    mov.refresh_from_db()

    mov.fecha = cuenta.fecha_conversion + timedelta(1)
    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=f'{errors.FECHA_POSTERIOR_A_CONVERSION}'
                  f'{cuenta.fecha_conversion} '
                  rf'\(es {cuenta.fecha_conversion + timedelta(1)}\)'
    ):
        mov.full_clean()
