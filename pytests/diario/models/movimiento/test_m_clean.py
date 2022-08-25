import pytest
from django.core.exceptions import ValidationError

from diario.models import Movimiento, Cuenta
from utils import errors


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
