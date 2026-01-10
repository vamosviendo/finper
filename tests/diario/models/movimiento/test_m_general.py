import pytest
from django.core.exceptions import ValidationError

from diario.models import Movimiento, Moneda
from utils.varios import el_que_no_es


def test_guarda_y_recupera_movimientos(fecha, dia, cuenta, cuenta_2):
    cantidad_movimientos = Movimiento.cantidad()
    mov = Movimiento()
    mov.dia = dia
    mov.concepto = 'entrada de efectivo'
    mov.importe = 985.5
    mov.cta_entrada = cuenta
    mov.cta_salida = cuenta_2
    mov.detalle = "Detalle del movimiento"
    mov.moneda = cuenta.moneda
    mov.cotizacion = 1.0
    mov.sk = "movsk"
    mov.save()

    assert Movimiento.cantidad() == cantidad_movimientos + 1

    mov_guardado = Movimiento.tomar(pk=mov.pk)

    assert mov_guardado.dia == dia
    assert mov_guardado.fecha == dia.fecha
    assert mov_guardado.concepto == 'entrada de efectivo'
    assert mov_guardado.importe == 985.5
    assert mov_guardado.cta_entrada == cuenta
    assert mov_guardado.cta_salida == cuenta_2
    assert mov_guardado.detalle == "Detalle del movimiento"
    assert mov_guardado.moneda == cuenta.moneda
    assert mov_guardado.cotizacion == 1.0
    assert mov_guardado.sk == "movsk"


def test_cta_entrada_se_relaciona_con_cuenta(cuenta, fecha):
    mov = Movimiento(fecha=fecha, concepto='Cobranza en efectivo', importe=100)
    mov.cta_entrada = cuenta
    mov.clean_save()
    assert mov in cuenta.entradas.all()


def test_cta_salida_se_relaciona_con_cuenta(cuenta, fecha):
    mov = Movimiento(fecha=fecha, concepto='Pago en efectivo', importe=100)
    mov.cta_salida = cuenta
    mov.clean_save()
    assert mov in cuenta.salidas.all()


def test_se_relaciona_con_dia(cuenta, importe, dia):
    mov = Movimiento(concepto='Entrada', importe=importe, cta_entrada=cuenta)
    mov.dia = dia
    mov.clean_save()
    assert mov in dia.movimiento_set.all()


def test_movimientos_se_ordenan_por_dia(entrada, entrada_tardia, entrada_anterior):
    assert list(Movimiento.todes()) == [entrada_anterior, entrada, entrada_tardia]


def test_dentro_del_dia_movimientos_se_ordenan_por_campo_orden_dia(cuenta, dia):
    mov1 = Movimiento.crear(
        dia=dia,
        concepto='Mov1',
        importe=100,
        cta_salida=cuenta,
    )
    mov2 = Movimiento.crear(
        dia=dia,
        concepto='Mov2',
        importe=100,
        cta_entrada=cuenta,
    )
    mov3 = Movimiento.crear(
        dia=dia,
        concepto='Mov3',
        importe=243,
        cta_entrada=cuenta,
    )

    mov3.orden_dia = 0
    mov3.clean_save()
    mov1.refresh_from_db()
    mov2.refresh_from_db()

    assert list(Movimiento.todes()) == [mov3, mov1, mov2]


def test_moneda_base_es_moneda_por_defecto(cuenta, fecha, mock_moneda_base):
    mov = Movimiento(fecha=fecha, concepto='Pago en efectivo', importe=100, cta_entrada=cuenta)
    mov.clean_save()
    assert mov.moneda == Moneda.tomar(sk=mock_moneda_base)


def test_cotizacion_por_defecto_es_1_para_cuentas_con_la_misma_moneda(cuenta, cuenta_2, fecha):
    mov = Movimiento(
        fecha=fecha, concepto="Movimiento entre cuentas en la misma moneda", importe=100,
        cta_entrada=cuenta, cta_salida=cuenta_2
    )
    mov.clean_save()
    assert mov.cotizacion == 1


@pytest.mark.parametrize("sentido", ["cta_entrada", "cta_salida"])
def test_en_movimientos_de_entrada_o_salida_cotizacion_es_siempre_uno(cuenta, fecha, sentido):
    kwargs = {
        'fecha': fecha,
        'concepto': 'Entrada o salida',
        'importe': 100,
        sentido: cuenta,
        'cotizacion': 50
    }
    mov = Movimiento(**kwargs)
    mov.clean_save()
    assert mov.cotizacion == 1


def test_en_movimientos_entre_cuentas_en_la_misma_moneda_cotizacion_es_siempre_uno(cuenta, cuenta_2, fecha):
    mov = Movimiento(
        fecha=fecha, concepto="Movimiento entre cuentas en la misma moneda", importe=100,
        cta_entrada=cuenta, cta_salida=cuenta_2, cotizacion=55
    )
    mov.clean_save()
    assert mov.cotizacion == 1


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_entre_cuentas_en_distinta_moneda_se_calcula_cotizacion_a_partir_de_la_cotizacion_de_ambas_monedas_a_la_fecha_del_movimiento(
        sentido, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros, dolar, euro,
        cotizacion_dolar, cotizacion_posterior_dolar, cotizacion_euro, cotizacion_posterior_euro, fecha):
    compra = sentido == "salida"
    sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")

    mov = Movimiento(
        fecha=fecha, concepto="Compra de dólares con euros", importe=100,
        moneda=euro
    )
    setattr(mov, f"cta_{sentido}", cuenta_con_saldo_en_dolares)
    setattr(mov, f"cta_{sentido_opuesto}", cuenta_con_saldo_en_euros)

    mov.clean_save()

    assert mov.cotizacion == euro.cotizacion_en_al(dolar, fecha, compra=compra)


def test_entre_cuentas_en_distinta_moneda_permite_especificar_cotizacion(
        cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros, dolar, euro,
        cotizacion_dolar, cotizacion_posterior_dolar, cotizacion_euro, cotizacion_posterior_euro, fecha):
    mov = Movimiento(
        fecha=fecha, concepto="Compra de dólares con euros", importe=100,
        cta_entrada=cuenta_con_saldo_en_dolares, cta_salida=cuenta_con_saldo_en_euros,
        moneda=euro
    )
    mov.cotizacion = 555
    mov.clean_save()
    assert mov.cotizacion == 555


def test_natural_key_devuelve_fecha_y_orden_dia(entrada, dia):
    assert entrada.natural_key() == (entrada.dia.fecha, entrada.orden_dia, )


def test_no_permite_clave_secundaria_duplicada(entrada, dia, cuenta):
    entrada.sk = "entradask"
    entrada.clean_save()

    mov = Movimiento(dia=dia, concepto="otro movimiento", importe=981, cta_entrada=cuenta)
    mov.sk = "entradask"

    with pytest.raises(ValidationError):
        mov.full_clean()


def test_genera_sk_a_partir_de_dia_y_orden_dia(dia, cuenta):
    mov = Movimiento(dia=dia, concepto="otro movimiento", importe=981, cta_entrada=cuenta)
    mov.clean_save()

    assert mov.sk == f"{mov.dia.sk}{mov.orden_dia:02d}"


def test_si_sk_generada_ya_existe_suma_1(entrada, salida, cuenta):
    entrada.delete()
    mov = Movimiento(dia=salida.dia, concepto="mov nuevo", importe=1, cta_entrada=cuenta)
    mov.clean_save()
    assert int(mov.sk) == int(salida.sk) + 1


def test_si_sk_generada_ya_existe_y_siguiente_tambien_sigue_sumando_hasta_encontrar_sk_libre(
        entrada, salida, traspaso, entrada_otra_cuenta, cuenta):
    entrada.delete()
    mov = Movimiento(dia=traspaso.dia, concepto="mov nuevo", importe=1, cta_entrada=cuenta, orden_dia=1)
    mov.clean_save()
    assert int(mov.sk) == int(entrada_otra_cuenta.sk) + 1


class TestCampoOrdenDia:

    # Fixtures

    @pytest.fixture
    def otra_entrada(self, cuenta, dia):
        return Movimiento.crear(
            concepto='Otra entrada', importe=120, cta_entrada=cuenta, dia=dia
        )

    @pytest.fixture
    def otra_salida(self, cuenta, dia):
        return Movimiento.crear(
            concepto='Otra salida', importe=12, cta_salida=cuenta, dia=dia
        )

    # Tests

    def test_se_genera_automaticamente(self, dia, cuenta):
        mov = Movimiento.crear(dia=dia, concepto="mov nuevo", importe=10, cta_entrada=cuenta)
        assert mov.orden_dia is not None

    def test_primer_mov_del_dia_tiene_orden_dia_cero(self, dia, cuenta):
        mov = Movimiento.crear(dia=dia, concepto="mov nuevo", importe=10, cta_entrada=cuenta)
        assert mov.orden_dia == 0

    def test_nuevo_movimiento_tiene_orden_dia_siguiente_al_ultimo_del_dia(self, dia, cuenta, entrada, salida):
        mov = Movimiento.crear(dia=dia, concepto="mov nuevo", importe=10, cta_entrada=cuenta)
        assert mov.orden_dia == 2

    def test_si_se_crea_movimiento_con_orden_dia_existente_movs_posteriores_suben_de_orden_dia(
            self, dia, cuenta, entrada, salida, traspaso):
        Movimiento.crear(
            dia=dia, concepto="mov nuevo", importe=10, cta_entrada=cuenta,
            orden_dia=1
        )
        salida.refresh_from_db()
        assert salida.orden_dia == 2

        traspaso.refresh_from_db()
        assert traspaso.orden_dia == 3

    def test_si_se_crea_movimiento_con_orden_dia_demasiado_alto_se_ajusta_al_ultimo_orden_dia_mas_uno(
            self, dia, cuenta, entrada, salida):
        mov = Movimiento.crear(
            dia=dia, concepto="mov nuevo", importe=10, cta_entrada=cuenta,
            orden_dia=10
        )
        assert mov.orden_dia == salida.orden_dia + 1

    def test_si_se_crea_movimiento_con_orden_dia_demasiado_alto_en_dia_sin_movimientos_se_ajusta_a_cero(
            self, dia, cuenta):
        mov = Movimiento.crear(
            dia=dia, concepto="mov nuevo", importe=10, cta_entrada=cuenta,
            orden_dia=10
        )
        assert mov.orden_dia == 0

    def test_si_se_elimina_movimiento_movimientos_posteriores_del_dia_bajan_de_orden(
            self, entrada, salida, traspaso):
        assert traspaso.orden_dia == 2

        salida.delete()
        traspaso.refresh_from_db()

        assert traspaso.orden_dia == 1

    def test_si_se_cambia_orden_dia_a_uno_anterior_movimientos_entre_orden_dia_anterior_y_nuevo_elevan_su_orden_dia(
            self, entrada, salida, traspaso, otra_salida, otra_entrada):
        otra_salida.orden_dia = 1
        otra_salida.clean_save()

        entrada.refresh_from_db()
        assert entrada.orden_dia == 0

        salida.refresh_from_db()
        assert salida.orden_dia == 2

        traspaso.refresh_from_db()
        assert traspaso.orden_dia == 3

        otra_entrada.refresh_from_db()
        assert otra_entrada.orden_dia == 4

    def test_si_se_cambia_orden_dia_a_uno_posterior_movimientos_entre_orden_dia_anterior_y_nuevo_bajan_su_orden_dia(
            self, entrada, salida, traspaso, otra_salida, otra_entrada):
        salida.orden_dia = 3
        salida.clean_save()

        entrada.refresh_from_db()
        assert entrada.orden_dia == 0

        traspaso.refresh_from_db()
        assert traspaso.orden_dia == 1

        otra_salida.refresh_from_db()
        assert otra_salida.orden_dia == 2

        otra_entrada.refresh_from_db()
        assert otra_entrada.orden_dia == 4

    def test_si_cambia_orden_dia_a_uno_demasiado_alto_se_ajusta_al_ultimo_mas_uno(self, entrada, salida, traspaso):
        traspaso.orden_dia = 5
        traspaso.clean_save()
        assert traspaso.orden_dia == 2

    def test_si_cambia_orden_dia_en_dia_con_un_solo_movimiento_se_acusta_a_cero(self, entrada):
        entrada.orden_dia = 5
        entrada.clean_save()
        assert entrada.orden_dia == 0

    def test_si_cambia_dia_a_uno_posterior_orden_dia_pasa_a_cero_y_se_mueve_orden_dia_de_movimientos_restantes_de_nuevo_dia(
            self, entrada, salida, dia_posterior, salida_posterior, traspaso_posterior):
        salida.dia = dia_posterior
        salida.clean_save()

        assert salida.orden_dia == 0

        salida_posterior.refresh_from_db()
        assert salida_posterior.orden_dia == 1

        traspaso_posterior.refresh_from_db()
        assert traspaso_posterior.orden_dia == 2

    def test_si_cambia_dia_a_uno_anterior_orden_dia_pasa_al_ultimo_del_nuevo_dia_mas_uno(
            self, entrada, salida, dia_anterior, entrada_anterior, entrada_anterior_otra_cuenta):
        salida.dia = dia_anterior
        salida.clean_save()

        assert salida.orden_dia == 2

        entrada_anterior.refresh_from_db()
        assert entrada_anterior.orden_dia == 0

        entrada_anterior_otra_cuenta.refresh_from_db()
        assert entrada_anterior_otra_cuenta.orden_dia == 1

    def test_si_cambia_dia_a_uno_anterior_y_orden_dia_no_toma_en_cuenta_orden_dia_cambiado(
            self, traspaso, entrada, salida, dia_anterior, entrada_anterior, entrada_anterior_otra_cuenta):
        entrada.dia = dia_anterior
        entrada.orden_dia = 0
        entrada.clean_save()

        assert entrada.orden_dia == 2

    def test_si_cambia_dia_a_uno_posterior_y_orden_dia_no_toma_en_cuenta_orden_dia_cambiado(
            self, traspaso, entrada, salida, dia_posterior, salida_posterior, traspaso_posterior):
        entrada.dia = dia_posterior
        entrada.orden_dia = 2
        entrada.clean_save()

        assert entrada.orden_dia == 0

        salida_posterior.refresh_from_db()
        assert salida_posterior.orden_dia == 1

        traspaso_posterior.refresh_from_db()
        assert traspaso_posterior.orden_dia == 2

    def test_si_cambia_dia_a_uno_anterior_sin_movimientos_orden_dia_pasa_a_cero(self, entrada, salida, dia_temprano):
        salida.dia = dia_temprano
        salida.clean_save()

        assert salida.orden_dia == 0

    def test_contramovimiento_credito_tiene_orden_dia_distinto_del_movimiento_originante(
            self, entrada, dia, cuenta, cuenta_ajena):
        mov = Movimiento.crear(
            dia=dia, concepto="prestamo", importe=10, cta_entrada=cuenta_ajena, cta_salida=cuenta,
        )

        contramov = Movimiento.tomar(id=mov.id_contramov)
        assert contramov.orden_dia != mov.orden_dia
        assert contramov.orden_dia == mov.orden_dia - 1
        assert entrada.orden_dia == 0

    def test_si_movimiento_normal_se_convierte_en_credito_el_contramovimiento_toma_orden_dia_distinto(
            self, traspaso, cuenta_ajena):
        traspaso.cta_entrada = cuenta_ajena
        traspaso.clean_save()

        contramov = Movimiento.tomar(id=traspaso.id_contramov)
        assert contramov.orden_dia != traspaso.orden_dia
        assert contramov.orden_dia == traspaso.orden_dia + 1

    def test_con_varios_movimientos(self, entrada_temprana, traspaso, entrada, salida, cuenta, cuenta_ajena, dia):
        mov = Movimiento.crear(
            concepto='Crédito',
            importe=128,
            cta_entrada=cuenta,
            cta_salida=cuenta_ajena,
            dia=dia,
        )
        contramov = Movimiento.tomar(id=mov.id_contramov)
        for cuenta in (entrada, salida, traspaso):
            cuenta.refresh_from_db()

        assert traspaso.orden_dia == 0
        assert entrada.orden_dia == 1
        assert salida.orden_dia == 2
        assert contramov.orden_dia == 3
        assert mov.orden_dia == 4
