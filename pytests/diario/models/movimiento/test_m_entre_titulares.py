import pytest

from diario.models import Movimiento, Cuenta


@pytest.fixture
def mock_gestionar_transferencia(mocker):
    return mocker.patch(
        'diario.models.Movimiento._gestionar_transferencia',
        autospec=True
    )


def test_movimiento_entre_titulares_gestiona_trasferencia(mock_gestionar_transferencia, cuenta, cuenta_ajena):
    mov = Movimiento(
        concepto='Préstamo',
        importe=10,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
    )
    mov.full_clean()
    mov.save()
    mock_gestionar_transferencia.assert_called_once_with(mov)


def test_movimiento_no_entre_titulares_no_gestiona_transferencia(mock_gestionar_transferencia, cuenta, cuenta_2):
    mov = Movimiento(
        concepto='Préstamo',
        importe=10,
        cta_entrada=cuenta,
        cta_salida=cuenta_2,
    )
    mov.full_clean()
    mov.save()
    mock_gestionar_transferencia.assert_not_called()


def test_no_gestiona_transferencia_si_esgratis(mock_gestionar_transferencia, cuenta, cuenta_ajena):
    mov = Movimiento(
        concepto='Prestamo', importe=10,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
    )
    mov.esgratis = True
    mov.full_clean()
    mov.save()
    mock_gestionar_transferencia.assert_not_called()


def test_integrativo_genera_cuenta_credito_y_subcuentas_y_movimiento(cuenta, cuenta_ajena):
    movimiento = Movimiento.crear(
        'Prestamo', 10, cta_entrada=cuenta, cta_salida=cuenta_ajena)
    assert Cuenta.cantidad() == 4
    assert Movimiento.cantidad() == 2

    cuenta_deudora = Cuenta.tomar(slug='_titular-otro')
    cuenta_acreedora = Cuenta.tomar(slug='_otro-titular')
    assert cuenta_acreedora.saldo == movimiento.importe
    assert cuenta_deudora.saldo == -cuenta_acreedora.saldo

    mov_credito = Movimiento.tomar(concepto='Constitución de crédito')
    assert mov_credito.detalle == 'de Otro Titular a Titular'
    assert mov_credito.importe == movimiento.importe
    assert mov_credito.cta_entrada == cuenta_acreedora
    assert mov_credito.cta_salida == cuenta_deudora
    assert mov_credito.cta_entrada.titular == movimiento.cta_salida.titular
    assert mov_credito.cta_salida.titular == movimiento.cta_entrada.titular


def test_integrativo_no_genera_nada_si_esgratis(cuenta, cuenta_ajena):
    Movimiento.crear(
        'Prestamo', 10,
        cta_entrada=cuenta, cta_salida=cuenta_ajena,
        esgratis=True
    )
    assert Cuenta.cantidad() == 2
    assert Movimiento.cantidad() == 1
