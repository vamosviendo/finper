from datetime import date

import pytest
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms import fields

from diario.forms import FormMovimiento
from diario.models import CuentaInteractiva
from utils import errors


@pytest.fixture
def formmov(cuenta: CuentaInteractiva, fecha: date) -> FormMovimiento:
    return FormMovimiento(data={
        'fecha': fecha,
        'concepto': 'movimiento bien formado',
        'importe': 150,
        'cta_entrada': cuenta,
    })


def test_acepta_movimientos_bien_formados(formmov):
    assert formmov.is_valid()


def test_no_acepta_movimientos_sin_cuentas(formmov):
    formmov.data.pop('cta_entrada')
    assert not formmov.is_valid()
    assert errors.CUENTA_INEXISTENTE in formmov.errors[NON_FIELD_ERRORS]


def test_no_acepta_cuentas_de_entrada_y_salida_iguales(formmov, cuenta):
    formmov.data.update({'cta_salida': cuenta})
    assert not formmov.is_valid()
    assert errors.CUENTAS_IGUALES in formmov.errors[NON_FIELD_ERRORS]


def test_no_acepta_conceptos_reservados(formmov):
    for c in ['movimiento correctivo',
              'Movimiento Correctivo',
              'MOVIMIENTO CORRECTIVO', ]:
        formmov.data.update({'concepto': c})
        assert \
            not formmov.is_valid(), \
            f'El concepto reservado "{c}" no debe pasar la verificación.'
        assert \
            f'El concepto "{c.lower()}" está reservado para su uso ' \
            f'por parte del sistema' in \
            formmov.errors['concepto']


def test_si_da_error_mov_sin_cuentas_no_da_error_cuentas_iguales(formmov):
    formmov.data.pop('cta_entrada')
    assert not formmov.is_valid()
    assert errors.CUENTAS_IGUALES not in formmov.errors[NON_FIELD_ERRORS]


def test_toma_fecha_del_dia_por_defecto(formmov):
    formmov.data.pop('fecha')
    assert formmov.fields['fecha'].initial() == date.today()


def test_muestra_campo_esgratis():
    formmov = FormMovimiento()
    assert 'esgratis' in formmov.fields.keys()
    assert isinstance(formmov.fields['esgratis'], fields.BooleanField)


def test_campo_esgratis_no_seleccionado_por_defecto():
    formmov = FormMovimiento()
    assert formmov.fields['esgratis'].initial is False


def test_campo_esgratis_aparece_seleccionado_si_instancia_no_tiene_contramovimiento(donacion):
    formmov = FormMovimiento(instance=donacion)
    assert formmov.fields['esgratis'].initial is True


def test_campo_esgratis_aparece_deseleccionado_si_instancia_tiene_contramovimiento(credito):
    formmov = FormMovimiento(instance=credito)
    assert formmov.fields['esgratis'].initial is False


def test_campo_esgratis_seleccionado_en_movimiento_entre_titulares_no_genera_movimiento_credito(
        mocker, formmov, cuenta_ajena):
    mock_crear_movimiento_credito = mocker.patch(
        'diario.forms.Movimiento._crear_movimiento_credito')
    formmov.data.update({'cta_salida': cuenta_ajena, 'esgratis': True})
    formmov.full_clean()
    formmov.save()
    mock_crear_movimiento_credito.assert_not_called()
