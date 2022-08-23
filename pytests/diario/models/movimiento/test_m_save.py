import pytest

from diario.models import Movimiento, Cuenta, CuentaInteractiva


@pytest.fixture
def credito_no_guardado(cuenta: CuentaInteractiva, cuenta_ajena: CuentaInteractiva) -> Movimiento:
    return Movimiento(
        concepto='Crédito',
        importe=30,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena
    )


def test_con_dos_cuentas_de_titulares_distintos_crea_dos_cuentas_credito(credito_no_guardado):
    credito_no_guardado.save()
    assert Cuenta.cantidad() == 4

    cc1 = list(Cuenta.todes())[-2]
    cc2 = list(Cuenta.todes())[-1]
    assert cc1.slug == '_otro-titular'
    assert cc2.slug == '_titular-otro'


def test_con_dos_cuentas_de_titulares_distintos_guarda_cuentas_credito_como_contracuentas(credito_no_guardado):
    credito_no_guardado.save()
    cta_acreedora, cta_deudora = list(Cuenta.todes())[-2:]
    assert cta_acreedora.contracuenta == cta_deudora
    assert cta_deudora.contracuenta == cta_acreedora


@pytest.mark.parametrize('campo_cuenta, fixt_cuenta', [
    ('cta_entrada', 'cuenta_ajena_2'),
    ('cta_salida', 'cuenta_2'),
])
def test_cambiar_cuenta_por_cta_mismo_titular_de_cuenta_opuesta_en_movimiento_de_traspaso_con_contramovimiento_destruye_contramovimiento(
        credito, campo_cuenta, fixt_cuenta, request):
    cuenta = request.getfixturevalue(fixt_cuenta)
    id_contramovimiento = credito.id_contramov

    setattr(credito, campo_cuenta, cuenta)
    credito.save()

    with pytest.raises(Movimiento.DoesNotExist):
        Movimiento.tomar(id=id_contramovimiento)

    assert credito.id_contramov is None


@pytest.mark.parametrize('campo_cuenta, slug_ce, slug_cs', [
    ('cta_entrada', '_otro-gordo', '_gordo-otro'),
    ('cta_salida', '_gordo-titular', '_titular-gordo'),
])
def test_cambiar_cuenta_de_movimiento_entre_titulares_por_cuenta_de_otro_titular_cambia_cuentas_en_contramovimiento(
        credito, campo_cuenta, slug_ce, slug_cs, titular_gordo):
    cuenta_gorda = Cuenta.crear(nombre="Cuenta gorda", slug="cg", titular=titular_gordo)
    setattr(credito, campo_cuenta, cuenta_gorda)
    credito.save()

    assert Movimiento.tomar(id=credito.id_contramov).cta_entrada.slug == slug_ce
    assert Movimiento.tomar(id=credito.id_contramov).cta_salida.slug == slug_cs


@pytest.mark.parametrize('campo_cuenta, fixt_cuenta', [
    ('cta_entrada', 'cuenta_2'),
    ('cta_salida', 'cuenta_ajena_2')
])
def test_cambiar_cuenta_de_movimiento_entre_titulares_por_cuenta_del_mismo_titular_no_cambia_cuentas_en_contramovimiento(
        credito, campo_cuenta, fixt_cuenta, request):
    cuenta = request.getfixturevalue(fixt_cuenta)
    contramov = Movimiento.tomar(id=credito.id_contramov)
    ce_contramov = contramov.cta_entrada
    cs_contramov = contramov.cta_salida

    setattr(credito, campo_cuenta, cuenta)
    credito.save()

    contramov = Movimiento.tomar(id=credito.id_contramov)
    assert contramov.cta_entrada == ce_contramov
    assert contramov.cta_salida == cs_contramov


@pytest.mark.parametrize('campo,fixt', [
    ('importe', 'importe_alto'),
    ('fecha', 'fecha_tardia'),
])
def test_cambiar_campo_sensible_de_movimiento_entre_titulares_cambia_el_mismo_campo_en_contramovimiento(
        credito, campo, fixt, request):
    valor = request.getfixturevalue(fixt)
    setattr(credito, campo, valor)
    credito.save()
    contramov = Movimiento.tomar(id=credito.id_contramov)
    assert getattr(contramov, campo) == valor
