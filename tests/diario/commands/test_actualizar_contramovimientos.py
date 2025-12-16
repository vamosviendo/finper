import pytest
from django.core.management import call_command

from diario.models import Movimiento


# Fixtures

@pytest.fixture
def otro_credito(cuenta, cuenta_ajena, dia_posterior):
    return Movimiento.crear(
        concepto='Otro crédito',
        importe=150,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
        dia=dia_posterior,
    )


# Tests

def test_reemplaza_detalle_por_concepto(credito, otro_credito):
    contramov_credito = Movimiento.tomar(id=credito.id_contramov)
    contramov_oc = Movimiento.tomar(id=otro_credito.id_contramov)

    contramov_credito.detalle = "Detalle contramov credito"
    contramov_credito.save()
    contramov_oc.detalle = "Detalle contramov otro crédito"
    contramov_oc.save()

    concepto_cc = contramov_credito.concepto
    concepto_coc = contramov_oc.concepto

    call_command("actualizar_contramovimientos")
    contramov_credito.refresh_from_db()
    contramov_oc.refresh_from_db()

    assert contramov_credito.detalle == concepto_cc
    assert contramov_oc.detalle == concepto_coc


def test_reemplaza_concepto_por_concepto_de_movimiento_origen(credito, otro_credito):
    contramov_credito = Movimiento.tomar(id=credito.id_contramov)
    contramov_oc = Movimiento.tomar(id=otro_credito.id_contramov)

    contramov_credito.concepto = "concepto contramov credito"
    contramov_credito.save()
    contramov_oc.concepto = "concepto contramov otro crédito"
    contramov_oc.save()

    call_command("actualizar_contramovimientos")
    contramov_credito.refresh_from_db()
    contramov_oc.refresh_from_db()

    assert contramov_credito.concepto == credito.concepto
    assert contramov_oc.concepto == otro_credito.concepto


def test_no_actualiza_movimientos_no_automaticos(credito, entrada, traspaso):
    detalle_credito = credito.detalle = "Detalle credito"
    concepto_credito = credito.concepto = "Concepto credito"
    credito.clean_save()
    detalle_entrada = entrada.detalle = "Detalle entrada"
    concepto_entrada = entrada.concepto = "Concepto entrada"
    entrada.clean_save()
    detalle_traspaso = traspaso.detalle = "Detalle traspaso"
    concepto_traspaso = traspaso.concepto = "Concepto traspaso"
    traspaso.clean_save()

    call_command("actualizar_contramovimientos")
    for mov in credito, entrada, traspaso:
        mov.refresh_from_db()

    assert credito.detalle == detalle_credito
    assert credito.concepto == concepto_credito
    assert entrada.detalle == detalle_entrada
    assert entrada.concepto == concepto_entrada
    assert traspaso.detalle == detalle_traspaso
    assert traspaso.concepto == concepto_traspaso
