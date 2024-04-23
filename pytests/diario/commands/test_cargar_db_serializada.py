from pathlib import Path

import pytest
from django.core.management import call_command

from diario.models import Titular, Moneda, Cuenta, Dia, Movimiento, CuentaAcumulativa, CuentaInteractiva, Saldo
from diario.serializers import CuentaSerializada, MovimientoSerializado
from finper import settings
from vvmodel.serializers import SerializedDb


def _tomar_movimiento(movimiento: MovimientoSerializado) -> Movimiento:
    return Movimiento.tomar(
        dia=Dia.tomar(fecha=movimiento.fields["dia"][0]),
        concepto=movimiento.fields["concepto"],
        detalle=movimiento.fields["detalle"],
        _importe=movimiento.fields["_importe"],
        cta_entrada=Cuenta.tomar(
            slug=movimiento.fields["cta_entrada"][0]
        ) if movimiento.fields["cta_entrada"] else None,
        cta_salida=Cuenta.tomar(
            slug=movimiento.fields["cta_salida"][0]
        ) if movimiento.fields["cta_salida"] else None,
    )


def _testear_movimiento(movimiento: MovimientoSerializado):
    try:
        _tomar_movimiento(movimiento)
    except Movimiento.DoesNotExist:
        raise AssertionError(
            f"Movimiento {movimiento.fields['orden_dia']} del {movimiento.fields['dia'][0]} "
            f"({movimiento.fields['concepto']} - {movimiento.fields['cta_salida']} "
            f"-> {movimiento.fields['cta_entrada']} {movimiento.fields['_importe']}) no cargado"
        )


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
        "Traspaso de saldo a subcuenta agregada 3", 11,
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
        "Traspaso de saldo a subcuenta agregada 4", 11,
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


@pytest.fixture
def db_serializada_y_vacia(cargar_base_de_datos, db_serializada: SerializedDb, vaciar_db) -> SerializedDb:
    """ Genera una base de datos, la serializa y borra el contenido de la base de datos"""
    return db_serializada


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


def test_carga_todas_las_cuentas_en_la_base_de_datos(db_serializada_y_vacia):
    cuentas = db_serializada_y_vacia.filter_by_model("diario.cuenta")
    call_command("cargar_db_serializada")
    for cuenta in cuentas:
        try:
            Cuenta.tomar(slug=cuenta.fields["slug"])
        except Cuenta.DoesNotExist:
            raise AssertionError(f"No se creó cuenta con slug {cuenta.fields['slug']}")


def test_carga_cuentas_con_fecha_de_creacion_correcta(db_serializada_y_vacia):
    cuentas = db_serializada_y_vacia.filter_by_model("diario.cuenta")
    call_command("cargar_db_serializada")
    for cuenta in cuentas:
        assert \
            Cuenta.tomar(slug=cuenta.fields["slug"]).fecha_creacion.strftime("%Y-%m-%d") == \
            cuenta.fields["fecha_creacion"], \
            f"Error en fecha de creación de cuenta \"{cuenta.fields['nombre']} ({cuenta.fields['slug']})\""


def test_carga_cuentas_acumulativas_con_fecha_de_conversion_correcta(db_serializada_y_vacia):
    cuentas = db_serializada_y_vacia.filter_by_model("diario.cuentaacumulativa")
    call_command("cargar_db_serializada")
    for cuenta in cuentas:
        assert \
            CuentaAcumulativa.tomar(
                slug=db_serializada_y_vacia.primere("diario.cuenta", pk=cuenta.pk).fields["slug"]
            ).fecha_conversion.strftime("%Y-%m-%d") == \
            cuenta.fields["fecha_conversion"]


def test_al_cargar_cuenta_acumulativa_carga_movimientos_anteriores_en_los_que_haya_participado(db_serializada_y_vacia):
    cuentas = [
        x for x in db_serializada_y_vacia.filter_by_model("diario.cuenta")
        if x.pk in [x.pk for x in db_serializada_y_vacia.filter_by_model("diario.cuentaacumulativa")]
    ]
    call_command("cargar_db_serializada")
    for cuenta in cuentas:
        movs_cuenta = [
            x for x in MovimientoSerializado.todes(container=db_serializada_y_vacia)
            if x.fields["cta_entrada"] == [cuenta.fields["slug"]] or
               x.fields["cta_salida"] == [cuenta.fields["slug"]]
        ]
        for mov in movs_cuenta:
            _testear_movimiento(mov)


def test_carga_cuentas_con_titular_correcto(db_serializada_y_vacia):
    cuentas = CuentaSerializada.todes(container=db_serializada_y_vacia).filter_by_model("diario.cuenta")

    call_command("cargar_db_serializada")

    for cuenta in cuentas:
        cuenta_guardada = Cuenta.tomar(slug=cuenta.fields["slug"])
        try:
            titular = cuenta_guardada.titular.titname
        except AttributeError:
            titular = cuenta_guardada.titular_original.titname
        assert titular == cuenta.titname()


def test_carga_cuentas_con_moneda_correcta(db_serializada_y_vacia):
    cuentas = CuentaSerializada.todes(container=db_serializada_y_vacia).filter_by_model("diario.cuenta")

    call_command("cargar_db_serializada")

    for cuenta in cuentas:
        cuenta_guardada = Cuenta.tomar(slug=cuenta.fields["slug"])
        assert cuenta_guardada.moneda.monname == cuenta.fields["moneda"][0]


def test_carga_subcuentas_con_cta_madre_correcta(db_serializada_y_vacia):
    cuentas = CuentaSerializada.todes(container=db_serializada_y_vacia).filter_by_model("diario.cuenta")

    call_command("cargar_db_serializada")

    for cuenta in cuentas:
        cuenta_guardada = Cuenta.tomar(slug=cuenta.fields["slug"])
        if cuenta_guardada.cta_madre is not None:
            assert cuenta_guardada.cta_madre.slug == cuenta.fields["cta_madre"][0]


def test_crea_contramovimiento_al_crear_movimiento_de_credito(credito, db_serializada, vaciar_db):
    call_command("cargar_db_serializada")
    try:
        Movimiento.tomar(
            concepto="Constitución de crédito",
            _importe=credito.importe,
            dia=Dia.tomar(fecha=credito.fecha)
        )
    except Movimiento.DoesNotExist:
        pytest.fail("No se generó contramovimiento en movimiento de crédito")



def test_no_crea_contramovimiento_al_crear_movimiento_de_donacion(donacion, db_serializada, vaciar_db):
    call_command("cargar_db_serializada")
    try:
        Movimiento.tomar(
            concepto="Constitución de crédito",
            _importe=donacion.importe,
            dia=Dia.tomar(fecha=donacion.fecha)
        )
        pytest.fail("Se generó contramovimiento en movimiento de donación")
    except Movimiento.DoesNotExist:
        pass


def test_carga_todos_los_movimientos_en_la_base_de_datos(db_serializada_y_vacia):
    movimientos = db_serializada_y_vacia.filter_by_model("diario.movimiento")
    call_command("cargar_db_serializada")
    assert Movimiento.cantidad() > 0
    assert Movimiento.cantidad() == len(movimientos)
    for mov in movimientos:
        _testear_movimiento(mov)


def test_carga_movimientos_con_orden_dia_correcto(db_serializada_y_vacia):
    movimientos = db_serializada_y_vacia.filter_by_model("diario.movimiento")
    call_command("cargar_db_serializada")
    for movimiento in movimientos:
        mov_creado = Movimiento.tomar(
            dia=Dia.tomar(fecha=movimiento.fields["dia"][0]),
            orden_dia=movimiento.fields["orden_dia"]
        )
        slug_cta_entrada = mov_creado.cta_entrada.slug if mov_creado.cta_entrada else None
        slug_cta_salida = mov_creado.cta_salida.slug if mov_creado.cta_salida else None
        assert (
            mov_creado.concepto,
            mov_creado.importe,
            slug_cta_entrada,
            slug_cta_salida,
        ) == (
            movimiento.fields["concepto"],
            movimiento.fields["_importe"],
            movimiento.fields["cta_entrada"][0] if movimiento.fields["cta_entrada"] else None,
            movimiento.fields["cta_salida"][0] if movimiento.fields["cta_salida"] else None,
        )


@pytest.mark.xfail
def test_divide_correctamente_cuentas_con_saldo_negativo():
    pytest.fail("escribir, y reescribir el nombre del test, y ubicar correctamente.")
