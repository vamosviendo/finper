from pathlib import Path

import pytest
from django.core.management import call_command

from diario.models import Titular, Moneda, Cuenta, Dia, Movimiento, CuentaAcumulativa, CuentaInteractiva, Saldo
from finper import settings


@pytest.fixture
def cuenta_temprana_1(titular: Titular, dia_temprano: Dia, peso: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        "cuenta temprana 1", "ct1",
        fecha_creacion=dia_temprano.fecha, titular=titular, moneda=peso
    )


@pytest.fixture
def cuenta_temprana_2(titular: Titular, dia_temprano: Dia, peso: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        "cuenta temprana 2", "ct2",
        fecha_creacion=dia_temprano.fecha, titular=titular, moneda=peso
    )


@pytest.fixture
def movimiento_temprano_1(cuenta_temprana_1: CuentaInteractiva, dia_temprano: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto="Saldo al inicio", importe=120,
        cta_entrada=cuenta_temprana_1, dia=dia_temprano
    )


@pytest.fixture
def movimiento_temprano_2(cuenta_temprana_2: CuentaInteractiva, dia_temprano: Dia) -> Movimiento:
    return Movimiento.crear(
        concepto="Saldo al inicio", importe=335,
        cta_entrada=cuenta_temprana_2, dia=dia_temprano
    )


@pytest.fixture
def cuenta_temprana_acumulativa(titular: Titular, dia_temprano: Dia, peso: Moneda) -> CuentaAcumulativa:
    cuenta = Cuenta.crear(
        "cuenta temprana acum", "cta",
        fecha_creacion=dia_temprano.fecha, titular=titular, moneda=peso
    )
    return cuenta.dividir_y_actualizar(
        ['subcuenta 1 cuenta temprana acum', 'sc1cta', 0],
        ['subcuenta 2 cuenta temprana acum', 'sc2cta'],
        fecha=cuenta.fecha_creacion
    )


@pytest.fixture
def movimiento_subcuenta_temprana_1(
        cuenta_temprana_acumulativa: CuentaAcumulativa,
        dia_temprano: Dia, ) -> Movimiento:
    return Movimiento.crear(
        concepto="Saldo al inicio", importe=54,
        cta_entrada=cuenta_temprana_acumulativa.subcuentas.first(), dia=dia_temprano
    )


@pytest.fixture
def movimiento_subcuenta_temprana_2(
        cuenta_temprana_acumulativa: CuentaAcumulativa,
        dia_temprano: Dia, ) -> Movimiento:
    return Movimiento.crear(
        concepto="Saldo al inicio", importe=86,
        cta_entrada=cuenta_temprana_acumulativa.subcuentas.last(), dia=dia_temprano
    )


@pytest.fixture
def dia_1(
        movimiento_temprano_1: Movimiento,
        movimiento_temprano_2: Movimiento,
        movimiento_subcuenta_temprana_1: Movimiento,
        movimiento_subcuenta_temprana_2: Movimiento,
        dia_temprano: Dia, ) -> Dia:
    return dia_temprano


@pytest.fixture
def movimiento_anterior_1(
        cuenta_temprana_1: CuentaInteractiva,
        dia_anterior: Dia, ) -> Movimiento:
    return Movimiento.crear(
        concepto="Entrada en cuenta temprana 1", importe=86,
        cta_entrada=cuenta_temprana_1, dia=dia_anterior
    )


@pytest.fixture
def dia_2(
        movimiento_anterior_1: Movimiento,
        dia_anterior: Dia, ) -> Dia:
    return dia_anterior


@pytest.fixture
def movimiento_1(
        cuenta_temprana_2: CuentaInteractiva,
        dia: Dia, ) -> Movimiento:
    return Movimiento.crear(
        concepto='Salida de cuenta temprana 2', importe=18,
        cta_salida=cuenta_temprana_2, dia=dia
    )

@pytest.fixture
def movimiento_2(
        cuenta_temprana_1: CuentaInteractiva,
        cuenta_temprana_2: CuentaInteractiva,
        dia: Dia, ) -> Movimiento:
    return Movimiento.crear(
        concepto='Traspaso de cuenta temprana 1 a cuenta temprana 2', importe=38,
        cta_entrada=cuenta_temprana_2, cta_salida=cuenta_temprana_1, dia=dia
    )


@pytest.fixture
def cuenta_2_acumulativa(cuenta_temprana_2: CuentaInteractiva, dia: Dia) -> CuentaAcumulativa:
    return cuenta_temprana_2.dividir_y_actualizar(
        ['subcuenta 1 cuenta 2 acum', 'sc1c2a', 23],
        ['subcuenta 2 cuenta 2 acum', 'sc2c2a'],
        fecha=dia.fecha,
)


@pytest.fixture
def subcuenta_agregada_3(
        cuenta_2_acumulativa: CuentaAcumulativa, otro_titular: Titular, dia: Dia) -> CuentaInteractiva:
    return cuenta_2_acumulativa.agregar_subcuenta(
        "subcuenta 3 cuenta 2 acum", "sc3c2a", otro_titular,
        fecha=dia.fecha,
    )


@pytest.fixture
def subcuenta_agregada_4(
        cuenta_2_acumulativa: CuentaAcumulativa, titular_gordo: Titular, dia: Dia) -> CuentaInteractiva:
    return cuenta_2_acumulativa.agregar_subcuenta(
        "subcuenta 4 cuenta 2 acum", "sc4c2a", titular_gordo,
        fecha=dia.fecha,
    )


@pytest.fixture
def saldo_subcuenta_agregada_3(
        cuenta_2_acumulativa: CuentaAcumulativa,
        subcuenta_agregada_3: CuentaInteractiva,
        dia: Dia) -> Saldo:
    subcuenta_salida = cuenta_2_acumulativa.subcuentas.all()[1]
    return Movimiento.crear(
        "Traspaso de saldo", 11,
        cta_entrada=subcuenta_agregada_3, cta_salida=subcuenta_salida,
        dia=dia, esgratis=True,
    ).saldo_ce()


@pytest.fixture
def saldo_subcuenta_agregada_4(
        cuenta_2_acumulativa: CuentaAcumulativa,
        subcuenta_agregada_4: CuentaInteractiva,
        dia: Dia, ) -> Saldo:
    subcuenta_salida = cuenta_2_acumulativa.subcuentas.all()[1]
    return Movimiento.crear(
        "Traspaso de saldo", 11,
        cta_entrada=subcuenta_agregada_4, cta_salida=subcuenta_salida,
        dia=dia, esgratis=True,
    ).saldo_ce()


@pytest.fixture
def dia_3(
        movimiento_1: Movimiento,
        movimiento_2: Movimiento,
        saldo_subcuenta_agregada_3: Saldo,
        saldo_subcuenta_agregada_4: Saldo,
        dia: Dia, ) -> Dia:
    return dia


@pytest.fixture
def cuenta_posterior(otro_titular: Titular, dolar: Moneda, dia_posterior: Dia) -> CuentaInteractiva:
    return Cuenta.crear(
        "cuenta posterior", "cp",
        fecha_creacion=dia_posterior.fecha, titular=otro_titular, moneda=dolar,
    )

@pytest.fixture
def credito_posterior(
        cuenta_temprana_1: CuentaInteractiva,
        cuenta_posterior: CuentaInteractiva,
        dia_posterior: Dia, ) -> Movimiento:
    return Movimiento.crear(
        concepto='Crédito de titular a otro titular', importe=17,
        cta_entrada=cuenta_posterior, cta_salida=cuenta_temprana_1,
        dia=dia_posterior, esgratis=False
    )


@pytest.fixture
def donacion_posterior(
        cuenta_temprana_1: CuentaInteractiva,
        cuenta_posterior: CuentaInteractiva,
        dia_posterior: Dia,
) -> Movimiento:
    return Movimiento.crear(
        concepto='Donacion de titular a otro titular', importe=14,
        cta_entrada=cuenta_posterior, cta_salida=cuenta_temprana_1,
        dia=dia_posterior, esgratis=True
    )


@pytest.fixture
def dia_4(
        credito_posterior: Movimiento,
        donacion_posterior: Movimiento,
        dia_posterior: Dia, ) -> Dia:
    return dia_posterior


@pytest.fixture
def subcuenta_agregada_tardia_3(
        cuenta_temprana_acumulativa: CuentaAcumulativa,
        otro_titular: Titular,
        dia_tardio: Dia, ) -> CuentaInteractiva:
    return cuenta_temprana_acumulativa.agregar_subcuenta(
        "subcuenta 3 cuenta temprana acum", "sc3cta", otro_titular,
        fecha=dia_tardio.fecha,
    )


@pytest.fixture
def subcuenta_agregada_tardia_4(
        cuenta_temprana_acumulativa: CuentaAcumulativa,
        titular_gordo: Titular,
        dia_tardio: Dia, ) -> CuentaInteractiva:
    return cuenta_temprana_acumulativa.agregar_subcuenta(
        "subcuenta 4 cuenta temprana acum", "sc4cta", titular_gordo,
        fecha=dia_tardio.fecha,
    )


@pytest.fixture
def movimiento_subcuenta_agregada_tardia_3(
        subcuenta_agregada_tardia_3: CuentaInteractiva,
        dia_tardio: Dia, ) -> Movimiento:
    return Movimiento.crear(
        concepto="ingreso en subcuenta agregada tardía 3", importe=150,
        cta_entrada=subcuenta_agregada_tardia_3, fecha=dia_tardio.fecha,
    )


@pytest.fixture
def movimiento_subcuenta_agregada_tardia_4(
        subcuenta_agregada_tardia_4: CuentaInteractiva,
        dia_tardio: Dia, ) -> Movimiento:
    return Movimiento.crear(
        concepto="ingreso en subcuenta agregada tardía 3", importe=225,
        cta_entrada=subcuenta_agregada_tardia_4, fecha=dia_tardio.fecha,
    )


@pytest.fixture
def dia_5(
        movimiento_subcuenta_agregada_tardia_3: Movimiento,
        movimiento_subcuenta_agregada_tardia_4: Movimiento,
        dia_tardio: Dia
) -> Dia:
    return dia_tardio


@pytest.fixture
def cargar_base_de_datos(
        dia_1: Dia,
        dia_2: Dia,
        dia_3: Dia,
        dia_4: Dia,
        dia_5: Dia,
):
    pass


def test_vacia_la_base_de_datos_antes_de_cargar_datos_nuevos(mocker, vaciar_db):
    mock_unlink = mocker.patch("pathlib.Path.unlink", autospec=True)
    call_command("cargar_db_serializada")
    mock_unlink.assert_called_once_with(Path(settings.BASE_DIR / "db.sqlite3"), missing_ok=True)


def test_carga_todos_los_titulares_en_la_base_de_datos(titular, otro_titular, db_serializada, vaciar_db):
    tits = db_serializada.filter_by_model("diario.titular")
    call_command("cargar_db_serializada")
    for tit in tits:
        Titular.tomar(titname=tit.fields["titname"])


def test_carga_todas_las_monedas_en_la_base_de_datos(peso, dolar, euro, db_serializada, vaciar_db):
    monedas = db_serializada.filter_by_model("diario.moneda")
    call_command("cargar_db_serializada")
    for moneda in monedas:
        Moneda.tomar(monname=moneda.fields["monname"])


def test_carga_todas_las_cuentas_en_la_base_de_datos(cargar_base_de_datos, db_serializada, vaciar_db):
    cuentas = db_serializada.filter_by_model("diario.cuenta")
    import shutil
    shutil.copyfile("db_full.json", "db_test.json")
    call_command("cargar_db_serializada")
    for cuenta in cuentas:
        try:
            Cuenta.tomar(slug=cuenta.fields["slug"])
        except Cuenta.DoesNotExist:
            raise AssertionError(f"No se creó cuenta con slug {cuenta.fields['slug']}")


def test_carga_cuentas_con_fecha_de_creacion_correcta(cargar_base_de_datos, db_serializada, vaciar_db):
    cuentas = db_serializada.filter_by_model("diario.cuenta")
    call_command("cargar_db_serializada")
    for cuenta in cuentas:
        assert \
            Cuenta.tomar(slug=cuenta.fields["slug"]).fecha_creacion.strftime("%Y-%m-%d") == \
            cuenta.fields["fecha_creacion"], \
            f"Error en fecha de creación de cuenta \"{cuenta.fields['nombre']}\""


@pytest.mark.xfail
def test_carga_cuentas_con_titular_correcto():
    pytest.fail("escribir")
