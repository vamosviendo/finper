from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.core.management import call_command

from diario.models import Titular, Moneda, Cuenta, Dia, Movimiento, CuentaAcumulativa, CuentaInteractiva, Saldo
from diario.serializers import CuentaSerializada, MovimientoSerializado
from finper import settings
from utils.errors import ElementoSerializadoInexistente
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
def cuenta_2_acumulativa(cuenta_temprana_2: CuentaInteractiva, dia: Dia) -> CuentaAcumulativa:
    return cuenta_temprana_2.dividir_y_actualizar(
        ['subcuenta 1 cuenta 2 acum', 'sc1c2a', 23],
        ['subcuenta 2 cuenta 2 acum', 'sc2c2a'],
        fecha=dia.fecha,
)


@pytest.fixture
def cuenta_posterior(otro_titular: Titular, dolar: Moneda, dia_posterior: Dia) -> CuentaInteractiva:
    return Cuenta.crear(
        "cuenta posterior", "cp",
        fecha_creacion=dia_posterior.fecha, titular=otro_titular, moneda=dolar,
    )


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


def test_vacia_la_base_de_datos_antes_de_cargar_datos_nuevos(mocker, vaciar_db):
    mock_unlink = mocker.patch("pathlib.Path.unlink", autospec=True)
    mock_call_command = mocker.patch("diario.management.commands.cargar_db_serializada.call_command")
    call_command("cargar_db_serializada")
    mock_unlink.assert_called_once_with(Path(settings.BASE_DIR / "db.sqlite3"), missing_ok=True)
    mock_call_command.assert_called_once_with("migrate")


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


def test_carga_todas_las_cuentas_en_la_base_de_datos(
        cuenta, cuenta_2, cuenta_3, cuenta_4, db_serializada, vaciar_db):
    cuentas = db_serializada.filter_by_model("diario.cuenta")
    call_command("cargar_db_serializada")
    assert len(cuentas) > 0
    for cuenta in cuentas:
        try:
            Cuenta.tomar(slug=cuenta.fields["slug"])
        except Cuenta.DoesNotExist:
            raise AssertionError(f"No se creó cuenta con slug {cuenta.fields['slug']}")


def test_carga_cuentas_con_fecha_de_creacion_correcta(
        cuenta_temprana_1, cuenta, cuenta_posterior, db_serializada, vaciar_db):
    cuentas = db_serializada.filter_by_model("diario.cuenta")
    call_command("cargar_db_serializada")
    assert len(cuentas) > 0
    for cuenta in cuentas:
        assert \
            Cuenta.tomar(slug=cuenta.fields["slug"]).fecha_creacion.strftime("%Y-%m-%d") == \
            cuenta.fields["fecha_creacion"], \
            f"Error en fecha de creación de cuenta \"{cuenta.fields['nombre']} ({cuenta.fields['slug']})\""


def test_carga_cuentas_acumulativas_con_fecha_de_conversion_correcta(
        cuenta_acumulativa, cuenta_temprana_acumulativa, cuenta_2_acumulativa, db_serializada, vaciar_db):
    cuentas = db_serializada.filter_by_model("diario.cuentaacumulativa")
    call_command("cargar_db_serializada")
    assert len(cuentas) > 0
    for cuenta in cuentas:
        assert \
            CuentaAcumulativa.tomar(
                slug=db_serializada.tomar(model="diario.cuenta", pk=cuenta.pk).fields["slug"]
            ).fecha_conversion.strftime("%Y-%m-%d") == \
            cuenta.fields["fecha_conversion"]


def test_al_cargar_cuenta_acumulativa_carga_movimientos_anteriores_en_los_que_haya_participado(
        movimiento_1, movimiento_2, cuenta_2_acumulativa, db_serializada, vaciar_db):
    cuentas = [
        x for x in db_serializada.filter_by_model("diario.cuenta")
        if x.pk in [x.pk for x in db_serializada.filter_by_model("diario.cuentaacumulativa")]
    ]
    call_command("cargar_db_serializada")
    assert len(cuentas) > 0
    for cuenta in cuentas:
        movs_cuenta = [
            x for x in MovimientoSerializado.todes(container=db_serializada)
            if x.fields["cta_entrada"] == [cuenta.fields["slug"]] or
               x.fields["cta_salida"] == [cuenta.fields["slug"]]
        ]
        assert len(movs_cuenta) > 0     # Puede fallar. Tal vez hay que puntualizar más o retirar
        for mov in movs_cuenta:
            _testear_movimiento(mov)


def test_si_al_cargar_movimientos_anteriores_de_cuenta_acumulativa_se_intenta_usar_una_cuenta_que_no_existe_da_error(
        movimiento_1, movimiento_2, cuenta_2_acumulativa, db_serializada, vaciar_db):
    db_sin_cta_1 = [x.data for x in db_serializada if x.fields.get("slug") != "ct1"]
    with open("db_full.json", "w") as f:
        json.dump(db_sin_cta_1, f)

    with pytest.raises(
            ElementoSerializadoInexistente,
            match="Elemento serializado 'ct1' de modelo 'diario.cuenta' inexistente"):
        call_command("cargar_db_serializada")


def test_si_al_cargar_movimientos_anteriores_de_cuenta_acumulativa_se_intenta_usar_una_cuenta_independiente_que_todavia_no_se_creo_se_la_crea_antes_de_generar_el_movimiento(
        movimiento_1, movimiento_2,
        cuenta_temprana_1,
        cuenta_2_acumulativa, db_serializada, vaciar_db):
    call_command("cargar_db_serializada")
    try:
        Cuenta.tomar(slug="ct1")
    except Cuenta.DoesNotExist:
        raise AssertionError(
            f"No se creó cuenta con slug ct1, ubicada después del movimiento en la serialización"
        )


def test_carga_cuentas_con_titular_correcto(cuenta, cuenta_ajena, cuenta_gorda, db_serializada, vaciar_db):
    cuentas = CuentaSerializada.todes(container=db_serializada).filter_by_model("diario.cuenta")

    call_command("cargar_db_serializada")

    assert len(cuentas) > 0
    for cuenta in cuentas:
        cuenta_guardada: Cuenta | CuentaAcumulativa = Cuenta.tomar(slug=cuenta.fields["slug"])
        try:
            titular = cuenta_guardada.titular.titname
        except AttributeError:
            titular = cuenta_guardada.titular_original.titname
        assert titular == cuenta.titname()


def test_carga_cuentas_con_moneda_correcta(
        cuenta, cuenta_en_euros, cuenta_en_dolares, cuenta_con_saldo_en_dolares,
        cuenta_acumulativa_en_dolares, cuenta_con_saldo_en_euros, db_serializada, vaciar_db):
    cuentas = CuentaSerializada.todes(container=db_serializada).filter_by_model("diario.cuenta")

    call_command("cargar_db_serializada")

    assert len(cuentas) > 0
    for cuenta in cuentas:
        cuenta_guardada = Cuenta.tomar(slug=cuenta.fields["slug"])
        assert cuenta_guardada.moneda.monname == cuenta.fields["moneda"][0]


def test_carga_subcuentas_con_cta_madre_correcta(cuenta_acumulativa, db_serializada, vaciar_db):
    cuentas = CuentaSerializada.todes(container=db_serializada).filter_by_model("diario.cuenta")
    subcuentas = SerializedDb([x for x in cuentas if x.fields["cta_madre"] is not None])
    call_command("cargar_db_serializada")

    assert len(subcuentas) > 0
    for cuenta in subcuentas:
        cuenta_guardada = Cuenta.tomar(slug=cuenta.fields["slug"])
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


def test_carga_todos_los_movimientos_en_la_base_de_datos(
        entrada, salida, entrada_anterior, salida_posterior, traspaso_posterior, db_serializada, vaciar_db):
    movimientos = db_serializada.filter_by_model("diario.movimiento")

    call_command("cargar_db_serializada")

    assert Movimiento.cantidad() > 0
    assert Movimiento.cantidad() == len(movimientos)
    assert len(movimientos) > 0
    for mov in movimientos:
        _testear_movimiento(mov)


def test_carga_movimientos_con_orden_dia_correcto(entrada, salida, traspaso, db_serializada, vaciar_db):
    movimientos = db_serializada.filter_by_model("diario.movimiento")
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


def test_carga_orden_dia_correcto_en_fechas_en_las_que_se_generaron_movimientos_automaticos(
        entrada, cuenta_acumulativa, salida, traspaso, db_serializada, vaciar_db):
    movimientos = db_serializada.filter_by_model("diario.movimiento")
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


def test_si_al_cargar_movimientos_generales_se_intenta_usar_una_cuenta_que_no_existe_da_error(
        movimiento_1, db_serializada, vaciar_db):
    db_sin_cta_2 = [x.data for x in db_serializada if x.fields.get("slug") != "ct2"]
    with open("db_full.json", "w") as f:
        json.dump(db_sin_cta_2, f)

    with pytest.raises(
            ElementoSerializadoInexistente,
            match="Elemento serializado 'ct2' de modelo 'diario.cuenta' inexistente"):
        call_command("cargar_db_serializada")

@pytest.mark.xfail
def test_divide_correctamente_cuentas_con_saldo_negativo():
    pytest.fail("escribir, y reescribir el nombre del test, y ubicar correctamente.")


@pytest.mark.xfail
def test_divide_correctamente_cuentas_sin_saldo():
    pytest.fail("escribir")


@pytest.mark.xfail
def test_crea_movimientos_de_traspaso_de_saldo_entre_cuentas_independientes_cuando_una_de_las_dos_cuentas_aun_no_ha_sido_creada():
    # Primero assert que una de las dos cuentas no existe en la bd al momento de crear el movimiento.
    # Después assert que existe el movimiento
    pytest.fail("escribir")


@pytest.mark.xfail
def test_crea_movimientos_de_traspaso_de_saldos_entre_dos_cuentas_independientes_ya_existentes():
    # Primero assert que las dos cuentas existen y el movimiento todavía no.
    # Después assert que existe el movimiento
    pytest.fail("escribir")

@pytest.mark.xfail
def test_crear_movimientos_a_partir_de_objetos_serializados(cuenta, cuenta_2, peso):
    from datetime import date
    m = Movimiento.crear(
        pk=2,
        fecha=date.today(),
        orden_dia=0,
        concepto='concepto',
        importe=110,
        cta_entrada=cuenta,
        cta_salida=cuenta_2,
        moneda=peso,
        # id_contramov=movimiento.fields['id_contramov'],
        # es_automatico=movimiento.fields['es_automatico'],
        # esgratis=movimiento.fields['id_contramov'] is None,
    )
    assert m.pk == 2
    assert m.orden_dia == 0
    m2 = Movimiento.crear(
        pk=4,
        fecha=date.today(),
        orden_dia=0,
        concepto='concepto',
        importe=110,
        cta_entrada=cuenta,
        cta_salida=cuenta_2,
        moneda=peso,
        # id_contramov=movimiento.fields['id_contramov'],
        # es_automatico=movimiento.fields['es_automatico'],
        # esgratis=movimiento.fields['id_contramov'] is None,
    )
    assert m2.pk == 4
    assert m2.orden_dia == 0
    assert m.orden_dia == m2.orden_dia  # BUG
    m3 = Movimiento.crear(
        fecha=date.today(),
        orden_dia=0,
        concepto='concepto',
        importe=110,
        cta_entrada=cuenta,
        cta_salida=cuenta_2,
        moneda=peso,
        # id_contramov=movimiento.fields['id_contramov'],
        # es_automatico=movimiento.fields['es_automatico'],
        # esgratis=movimiento.fields['id_contramov'] is None,
    )
    assert m3.pk == 5
    assert m3.orden_dia == m2.orden_dia == m.orden_dia      # BUG

    m3.pk = 6
    m3.full_clean()
    m3.save()
    # Acá falla porque evidentemente Django usa la primary key para otras
    # tareas que desconozco. Por eso, es mejor tener una primary key propia,
    # de la cual además no dependa el ordenamiento de los movimientos, como
    # ya tenemos en Cuenta, Titular, Moneda, etc.
    assert m3.pk == 6
