from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.core.management import call_command

from diario.models import (
    Titular,
    Moneda,
    Cotizacion,
    Cuenta,
    CuentaAcumulativa,
    CuentaInteractiva,
    Dia,
    Movimiento,
    SaldoDiario,
)
from diario.serializers import CuentaSerializada, MovimientoSerializado, TitularSerializado, MonedaSerializada
from finper import settings
from utils.errors import ElementoSerializadoInexistente
from vvmodel.serializers import SerializedDb


def _tomar_movimiento(movimiento: MovimientoSerializado) -> Movimiento:
    return Movimiento.tomar(
        fecha=movimiento.fields["dia"][0],
        concepto=movimiento.fields["concepto"],
        detalle=movimiento.fields["detalle"],
        _importe=movimiento.fields["_importe"],
        cta_entrada=Cuenta.tomar(
            sk=movimiento.fields["cta_entrada"][0]
        ) if movimiento.fields["cta_entrada"] else None,
        cta_salida=Cuenta.tomar(
            sk=movimiento.fields["cta_salida"][0]
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
def cuenta_temprana_acumulativa(titular: Titular, peso: Moneda) -> Cuenta | CuentaAcumulativa:
    cuenta = Cuenta.crear(
        "cuenta temprana acum", "cta",
        fecha_creacion=titular.fecha_alta, titular=titular, moneda=peso
    )
    return cuenta.dividir_y_actualizar(
        ['subcuenta 1 cuenta temprana acum', 'sc1cta', 0],
        ['subcuenta 2 cuenta temprana acum', 'sc2cta'],
        fecha=cuenta.fecha_creacion
    )


@pytest.fixture
def cuenta_2_acumulativa(cuenta_temprana_2: CuentaInteractiva, dia: Dia) -> Cuenta | CuentaAcumulativa:
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
def subcuenta_agregada_en_fecha_conversion_1(cuenta_acumulativa: CuentaAcumulativa) -> CuentaInteractiva:
    return cuenta_acumulativa.agregar_subcuenta(
        nombre="subcuenta agregada 1",
        sk="sca1",
        titular=cuenta_acumulativa.titular_original,
        fecha=cuenta_acumulativa.fecha_conversion
    )


@pytest.fixture
def subcuenta_agregada_en_fecha_conversion_2(cuenta_acumulativa: CuentaAcumulativa) -> CuentaInteractiva:
    return cuenta_acumulativa.agregar_subcuenta(
        nombre="subcuenta agregada 2",
        sk="sca2",
        titular=cuenta_acumulativa.titular_original,
        fecha=cuenta_acumulativa.fecha_conversion
    )


@pytest.fixture
def traspaso_a_subcuenta_agregada_1(
        cuenta_acumulativa: CuentaAcumulativa,
        subcuenta_agregada_en_fecha_conversion_1
) -> Movimiento:
    sco1 = cuenta_acumulativa.subcuentas.all()[0]
    return Movimiento.crear(
        "Traspaso de saldo a subcuenta agregada 1",
        cta_entrada=subcuenta_agregada_en_fecha_conversion_1,
        cta_salida=sco1,
        importe=20,
        fecha=cuenta_acumulativa.fecha_conversion
    )


@pytest.fixture
def traspaso_a_subcuenta_agregada_2(
        cuenta_acumulativa: CuentaAcumulativa,
        subcuenta_agregada_en_fecha_conversion_2
) -> Movimiento:
    sco1 = cuenta_acumulativa.subcuentas.all()[0]
    return Movimiento.crear(
        "Traspaso de saldo a subcuenta agregada 2",
        cta_entrada=subcuenta_agregada_en_fecha_conversion_2,
        cta_salida=sco1,
        importe=15,
        fecha=cuenta_acumulativa.fecha_conversion
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


def test_vacia_la_base_de_datos_antes_de_cargar_datos_nuevos(mocker, db_serializada_con_datos, vaciar_db):
    mock_unlink = mocker.patch("pathlib.Path.unlink", autospec=True)
    mock_call_command = mocker.patch("diario.management.commands.cargar_db_serializada.call_command")
    call_command("cargar_db_serializada")
    mock_unlink.assert_called_once_with(Path(settings.DATABASES["default"]["NAME"]), missing_ok=True)
    mock_call_command.assert_called_once_with("migrate")


class TestCargaTitulares:
    def test_carga_todos_los_titulares_en_la_base_de_datos(self, titular, otro_titular, db_serializada, vaciar_db):
        tits = TitularSerializado.todes(db_serializada).filter_by_model("diario.titular")
        call_command("cargar_db_serializada")
        for tit in tits:
            Titular.tomar(sk=tit.sk)

    def test_coyuntural_genera_campo_sk_a_partir_de_campo_titname(self, titular, otro_titular, db_serializada_legacy, vaciar_db):
        tits = db_serializada_legacy.filter_by_model("diario.titular")
        try:
            call_command("cargar_db_serializada")
        except TypeError:
            raise AssertionError("comando cargar_db_serializada no convierte campo 'titname' a 'sk'")

        for i, titular in enumerate(Titular.todes()):
            assert titular.sk == tits[i].fields["titname"]

class TestCargaMonedas:
    def test_carga_todas_las_monedas_en_la_base_de_datos(self, peso, dolar, euro, db_serializada, vaciar_db):
        monedas = MonedaSerializada.todes(db_serializada).filter_by_model("diario.moneda")
        call_command("cargar_db_serializada")
        for moneda in monedas:
            Moneda.tomar(sk=moneda.sk)


class TestCargaCotizaciones:
    def test_carga_todas_las_cotizaciones_en_la_base_de_datos(
            self, peso, dolar, euro, yen, cotizacion_posterior_dolar, cotizacion_tardia_dolar,
            db_serializada, vaciar_db):
        cotizaciones = db_serializada.filter_by_model("diario.cotizacion")
        call_command("cargar_db_serializada")
        assert Cotizacion.cantidad() == len(cotizaciones)
        for cotizacion in cotizaciones:
            try:
                Cotizacion.tomar(
                    moneda=Moneda.tomar(sk=cotizacion.fields["moneda"][0]),
                    fecha=cotizacion.fields["fecha"]
                )
            except Cotizacion.DoesNotExist:
                raise AssertionError(
                    f"No se creó cotización de moneda {cotizacion.sk} "
                    f"al {cotizacion.fields['fecha']}")


class TestCargaCuentas:
    def test_carga_todas_las_cuentas_en_la_base_de_datos(
            self, cuenta, cuenta_2, cuenta_3, cuenta_4, db_serializada, vaciar_db):
        cuentas = CuentaSerializada.todes(container=db_serializada).filter_by_model("diario.cuenta")
        call_command("cargar_db_serializada")
        assert len(cuentas) > 0
        for cuenta in cuentas:
            try:
                Cuenta.tomar(sk=cuenta.sk)
            except Cuenta.DoesNotExist:
                raise AssertionError(f"No se creó cuenta con sk {cuenta.sk}")

    def test_carga_cuentas_con_fecha_de_creacion_correcta(
            self, cuenta_temprana_1, cuenta, cuenta_posterior, db_serializada, vaciar_db):
        cuentas = CuentaSerializada.todes(container=db_serializada).filter_by_model("diario.cuenta")
        call_command("cargar_db_serializada")
        assert len(cuentas) > 0
        for cuenta in cuentas:
            assert \
                Cuenta.tomar(sk=cuenta.sk).fecha_creacion.strftime("%Y-%m-%d") == \
                cuenta.fields["fecha_creacion"], \
                f"Error en fecha de creación de cuenta \"{cuenta.fields['nombre']} ({cuenta.sk})\""

    def test_carga_cuentas_acumulativas_con_fecha_de_conversion_correcta(
            self, cuenta_acumulativa, cuenta_temprana_acumulativa, cuenta_2_acumulativa, db_serializada, vaciar_db):
        cuentas = CuentaSerializada.todes(container=db_serializada).filter_by_model("diario.cuentaacumulativa")
        call_command("cargar_db_serializada")
        assert len(cuentas) > 0
        for cuenta in cuentas:
            assert \
                CuentaAcumulativa.tomar(
                    sk=CuentaSerializada(db_serializada.tomar(model="diario.cuenta", pk=cuenta.pk)).sk
                ).fecha_conversion.strftime("%Y-%m-%d") == \
                cuenta.fields["fecha_conversion"]

    def test_al_cargar_cuenta_acumulativa_carga_movimientos_anteriores_en_los_que_haya_participado(
            self, movimiento_1, movimiento_2, cuenta_2_acumulativa, db_serializada, vaciar_db):
        cuentas = [
            CuentaSerializada(x) for x in db_serializada.filter_by_model("diario.cuenta")
            if x.pk in [x.pk for x in db_serializada.filter_by_model("diario.cuentaacumulativa")]
        ]
        call_command("cargar_db_serializada")
        assert len(cuentas) > 0
        for cuenta in cuentas:
            movs_cuenta = [
                x for x in MovimientoSerializado.todes(container=db_serializada)
                if x.fields["cta_entrada"] == [cuenta.sk] or x.fields["cta_salida"] == [cuenta.sk]
            ]
            assert len(movs_cuenta) > 0     # Puede fallar. Tal vez hay que puntualizar más o retirar
            for mov in movs_cuenta:
                _testear_movimiento(mov)

    def test_si_al_cargar_movimientos_anteriores_de_cuenta_acumulativa_se_intenta_usar_una_cuenta_que_no_existe_da_error(
            self, movimiento_1, movimiento_2, cuenta_2_acumulativa, db_serializada, vaciar_db):
        db_sin_cta_1 = [x.data for x in db_serializada if x.fields.get("sk") != "ct1"]
        with open("db_full.json", "w") as f:
            json.dump(db_sin_cta_1, f)

        with pytest.raises(
                ElementoSerializadoInexistente,
                match="Elemento serializado 'ct1' de modelo 'diario.cuenta' inexistente"):
            call_command("cargar_db_serializada")

    def test_si_al_cargar_movimientos_anteriores_de_cuenta_acumulativa_se_intenta_usar_una_cuenta_independiente_que_todavia_no_se_creo_se_la_crea_antes_de_generar_el_movimiento(
            self, movimiento_1, movimiento_2,
            cuenta_temprana_1,
            cuenta_2_acumulativa, db_serializada, vaciar_db):
        call_command("cargar_db_serializada")
        try:
            Cuenta.tomar(sk="ct1")
        except Cuenta.DoesNotExist:
            raise AssertionError(
                f"No se creó cuenta con sk ct1, ubicada después del movimiento en la serialización"
            )

    def test_carga_cuentas_con_titular_correcto(self, cuenta, cuenta_ajena, cuenta_gorda, db_serializada, vaciar_db):
        cuentas = CuentaSerializada.todes(container=db_serializada).filter_by_model("diario.cuenta")

        call_command("cargar_db_serializada")

        assert len(cuentas) > 0
        for cuenta in cuentas:
            cuenta_guardada = Cuenta.tomar(sk=cuenta.sk)
            try:
                titular = cuenta_guardada.titular.sk
            except AttributeError:
                titular = cuenta_guardada.titular_original.sk
            assert titular == cuenta.sk_tit()

    def test_carga_cuentas_con_moneda_correcta(
            self, cuenta, cuenta_en_euros, cuenta_en_dolares, cuenta_con_saldo_en_dolares,
            cuenta_acumulativa_en_dolares, cuenta_con_saldo_en_euros, db_serializada, vaciar_db):
        cuentas = CuentaSerializada.todes(container=db_serializada).filter_by_model("diario.cuenta")

        call_command("cargar_db_serializada")

        assert len(cuentas) > 0
        for cuenta in cuentas:
            cuenta_guardada = Cuenta.tomar(sk=cuenta.sk)
            assert cuenta_guardada.moneda.sk == cuenta.fields["moneda"][0]

    def test_carga_subcuentas_con_cta_madre_correcta(self, cuenta_acumulativa, db_serializada, vaciar_db):
        cuentas = CuentaSerializada.todes(container=db_serializada).filter_by_model("diario.cuenta")
        subcuentas = SerializedDb([x for x in cuentas if x.fields["cta_madre"] is not None])
        call_command("cargar_db_serializada")

        assert len(subcuentas) > 0
        for cuenta in subcuentas:
            cuenta_guardada = Cuenta.tomar(sk=cuenta.sk)
            assert cuenta_guardada.cta_madre.sk == cuenta.fields["cta_madre"][0]


class TestCargaSaldosDiarios:
    def test_crea_saldos_diarios_a_partir_de_movimientos(
            self, cuenta, entrada_anterior, entrada, salida, salida_posterior, db_serializada, vaciar_db):
        call_command("cargar_db_serializada")
        cuenta = Cuenta.tomar(sk=cuenta.sk)
        for m in Movimiento.todes():
            try:
                SaldoDiario.tomar(cuenta=cuenta, dia=m.dia)
            except SaldoDiario.DoesNotExist:
                raise AssertionError(f"Saldo diario de cuenta del día {m.dia} no se creó")

    def test_importe_del_saldo_diario_creado_es_igual_a_suma_de_los_importes_de_los_movimientos_de_la_cuenta_en_el_dia(
            self, cuenta, entrada, salida, traspaso, db_serializada, vaciar_db):
        call_command("cargar_db_serializada")
        cuenta = Cuenta.tomar(sk=cuenta.sk)
        dia = Dia.tomar(fecha=entrada.dia.fecha)
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=dia)
        assert \
            saldo_diario.importe == \
            entrada.importe_cta_entrada + salida.importe_cta_salida + traspaso.importe_cta_entrada


class TestCargaMovimientos:
    def test_crea_contramovimiento_al_crear_movimiento_de_credito(self, credito, db_serializada, vaciar_db):
        call_command("cargar_db_serializada")
        try:
            Movimiento.tomar(
                concepto="Constitución de crédito",
                _importe=credito.importe,
                fecha=credito.fecha
            )
        except Movimiento.DoesNotExist:
            pytest.fail("No se generó contramovimiento en movimiento de crédito")

    def test_no_crea_contramovimiento_al_crear_movimiento_de_donacion(self, donacion, db_serializada, vaciar_db):
        call_command("cargar_db_serializada")
        mov = Movimiento.tomar(fecha=donacion.fecha, orden_dia=donacion.orden_dia)
        try:
            Movimiento.tomar(
                concepto="Constitución de crédito",
                _importe=donacion.importe,
                fecha=donacion.fecha
            )
            pytest.fail("Se generó contramovimiento en movimiento de donación")
        except Movimiento.DoesNotExist:
            pass
        assert mov.id_contramov is None

    def test_carga_todos_los_movimientos_en_la_base_de_datos(
            self, entrada, salida, entrada_anterior, salida_posterior, traspaso_posterior, db_serializada, vaciar_db):
        movimientos = db_serializada.filter_by_model("diario.movimiento")

        call_command("cargar_db_serializada")

        assert Movimiento.cantidad() > 0
        assert Movimiento.cantidad() == len(movimientos)
        assert len(movimientos) > 0
        for mov in movimientos:
            _testear_movimiento(mov)

    def test_carga_movimientos_con_orden_dia_correcto(self, entrada, salida, traspaso, db_serializada, vaciar_db):
        movimientos = db_serializada.filter_by_model("diario.movimiento")
        call_command("cargar_db_serializada")
        for movimiento in movimientos:
            mov_creado = Movimiento.tomar(
                fecha=movimiento.fields["dia"][0],
                orden_dia=movimiento.fields["orden_dia"]
            )
            sk_cta_entrada = mov_creado.cta_entrada.sk if mov_creado.cta_entrada else None
            sk_cta_salida = mov_creado.cta_salida.sk if mov_creado.cta_salida else None
            assert (
                mov_creado.concepto,
                mov_creado.importe,
                sk_cta_entrada,
                sk_cta_salida,
            ) == (
                movimiento.fields["concepto"],
                movimiento.fields["_importe"],
                movimiento.fields["cta_entrada"][0] if movimiento.fields["cta_entrada"] else None,
                movimiento.fields["cta_salida"][0] if movimiento.fields["cta_salida"] else None,
            )

    def test_carga_movimientos_con_cotizacion_correcta(self, venta_dolares, request):
        venta_dolares.cotizacion = 666.66
        venta_dolares.clean_save()
        request.getfixturevalue("db_serializada")
        request.getfixturevalue("vaciar_db")
        call_command("cargar_db_serializada")
        mov_creado = Movimiento.tomar(
            fecha=venta_dolares.fecha,
            orden_dia=venta_dolares.orden_dia
        )
        assert mov_creado.cotizacion == 666.66

    def test_carga_cotizacion_correcta_en_movimientos_anteriores_de_cuentas_acumulativas(
            self, cuenta_en_dolares, venta_dolares, fecha, request):
        venta_dolares.cotizacion = 666.66
        venta_dolares.clean_save()
        cuenta_en_dolares.dividir_y_actualizar(
            ['subcuenta 1 con saldo en dólares', 'scsd1', 0],
            ['subcuenta 2 con saldo en dólares', 'scsd2'],
            fecha=fecha
        )
        request.getfixturevalue("db_serializada")
        request.getfixturevalue("vaciar_db")

        call_command("cargar_db_serializada")

        mov_creado = Movimiento.tomar(
            fecha=venta_dolares.fecha,
            orden_dia=venta_dolares.orden_dia
        )

        assert mov_creado.cotizacion == 666.66

    def test_carga_orden_dia_correcto_en_fechas_en_las_que_se_generaron_movimientos_automaticos(
            self, entrada, cuenta_acumulativa, salida, traspaso, db_serializada, vaciar_db):
        movimientos = db_serializada.filter_by_model("diario.movimiento")
        call_command("cargar_db_serializada")
        for movimiento in movimientos:
            mov_creado = Movimiento.tomar(
                fecha=movimiento.fields["dia"][0],
                orden_dia=movimiento.fields["orden_dia"]
            )
            sk_cta_entrada = mov_creado.cta_entrada.sk if mov_creado.cta_entrada else None
            sk_cta_salida = mov_creado.cta_salida.sk if mov_creado.cta_salida else None
            assert (
                mov_creado.concepto,
                mov_creado.importe,
                sk_cta_entrada,
                sk_cta_salida,
            ) == (
                movimiento.fields["concepto"],
                movimiento.fields["_importe"],
                movimiento.fields["cta_entrada"][0] if movimiento.fields["cta_entrada"] else None,
                movimiento.fields["cta_salida"][0] if movimiento.fields["cta_salida"] else None,
            )

    def test_si_al_cargar_movimientos_generales_se_intenta_usar_una_cuenta_que_no_existe_da_error(
            self, movimiento_1, db_serializada, vaciar_db):
        db_sin_cta_2 = [x.data for x in db_serializada if x.fields.get("sk") != "ct2"]
        with open("db_full.json", "w") as f:
            json.dump(db_sin_cta_2, f)

        with pytest.raises(
                ElementoSerializadoInexistente,
                match="Elemento serializado 'ct2' de modelo 'diario.cuenta' inexistente"):
            call_command("cargar_db_serializada")


class TestDivideCuentas:
    def test_divide_correctamente_cuentas_con_saldo_negativo(
            self, cuenta_acumulativa_saldo_negativo, db_serializada, vaciar_db):
        call_command("cargar_db_serializada")
        cuenta_recuperada = Cuenta.tomar(sk=cuenta_acumulativa_saldo_negativo.sk)
        assert cuenta_recuperada.es_acumulativa
        assert cuenta_recuperada.saldo() == -100
        subcuentas = cuenta_recuperada.subcuentas.all()
        assert len(subcuentas) == 2
        assert subcuentas[0].nombre == "subcuenta 1 saldo negativo"
        assert subcuentas[0].sk == "scsn1"
        assert subcuentas[0].saldo() == -10
        assert subcuentas[1].saldo() == cuenta_recuperada.saldo() + 10

    def test_divide_correctamente_cuentas_sin_saldo(self, cuenta_acumulativa_saldo_0, db_serializada, vaciar_db):
        call_command("cargar_db_serializada")
        cuenta_recuperada = Cuenta.tomar(sk=cuenta_acumulativa_saldo_0.sk)
        assert cuenta_recuperada.es_acumulativa
        assert cuenta_recuperada.saldo() == 0
        subcuentas = cuenta_recuperada.subcuentas.all()
        assert len(subcuentas) == 2
        assert subcuentas[0].nombre == "subcuenta 1 saldo 0"
        assert subcuentas[0].sk == "sc1"
        assert subcuentas[0].saldo() == 0
        assert subcuentas[1].saldo() == 0

    def test_recupera_correctamente_subcuentas_de_origen_y_subcuentas_agregadas_en_la_misma_fecha_de_la_division(
            self,
            cuenta_acumulativa,
            subcuenta_agregada_en_fecha_conversion_1,
            subcuenta_agregada_en_fecha_conversion_2,
            traspaso_a_subcuenta_agregada_1,
            traspaso_a_subcuenta_agregada_2,
            db_serializada, vaciar_db,
    ):
        call_command("cargar_db_serializada")
        ca = cuenta_acumulativa.tomar_del_sk()
        sco1, sco2, sca1, sca2 = ca.subcuentas.all()
        assert sco1.saldo() == 60-20-15
        assert sco2.saldo() == 40
        assert sca1.saldo() == 20
        assert sca2.saldo() == 15

        traspaso_1 = Movimiento.tomar(concepto="Traspaso de saldo a subcuenta agregada 1")
        traspaso_2 = Movimiento.tomar(concepto="Traspaso de saldo a subcuenta agregada 2")
        assert traspaso_1.importe == 20
        assert traspaso_1.cta_entrada == sca1
        assert traspaso_1.cta_salida == sco1
        assert traspaso_1.fecha == ca.fecha_conversion
        assert traspaso_2.importe == 15
        assert traspaso_2.cta_entrada == sca2
        assert traspaso_2.cta_salida == sco1
        assert traspaso_2.fecha == ca.fecha_conversion

    def test_crea_contramovimiento_de_movimiento_de_traspaso_de_saldo_no_gratuito_al_dividir_cuenta_en_subcuentas_de_distinto_titular(
            self, cuenta_de_dos_titulares, db_serializada, vaciar_db):
        call_command("cargar_db_serializada")
        cuenta_otro_titular = Cuenta.tomar(sk="sctg")
        traspaso = cuenta_otro_titular.movs().first()
        assert traspaso.id_contramov is not None
        contramov = Movimiento.tomar(pk=traspaso.id_contramov)
        assert contramov.importe == traspaso.importe

    def test_no_crea_contramovimiento_de_movimiento_de_traspaso_de_saldo_gratuito_al_dividir_cuenta_en_subcuentas_de_distinto_titular(
            self, division_gratuita, db_serializada, vaciar_db):
        call_command("cargar_db_serializada")
        cuenta_otro_titular = Cuenta.tomar(sk="sctg")
        traspaso = cuenta_otro_titular.movs().first()
        assert traspaso.id_contramov is None
