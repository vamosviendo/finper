from typing import Tuple
from unittest.mock import call

import pytest
from django.forms.models import model_to_dict

from diario.models import Cuenta, CuentaInteractiva, Dia, Movimiento, SaldoDiario
from utils.helpers_tests import \
    cambiar_fecha, dividir_en_dos_subcuentas, signo
from utils.varios import el_que_no_es


def inferir_fixtures(sentido: str, request) -> Tuple[Movimiento, int, CuentaInteractiva]:
    mov = request.getfixturevalue(sentido)
    return mov, signo(sentido == 'entrada'), getattr(mov, f'cta_{sentido}')


@pytest.fixture
def credito_no_guardado(cuenta: CuentaInteractiva, cuenta_ajena: CuentaInteractiva, dia: Dia) -> Movimiento:
    return Movimiento(
        concepto='Crédito',
        importe=30,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
        dia=dia,
    )


class TestSaveGeneral:
    def test_no_modifica_saldo_en_mov_si_no_se_modifica_importe_ni_cuentas_ni_fecha(
            self, traspaso, mocker):
        mock_saldo_save = mocker.patch('diario.models.movimiento.SaldoDiario.save')
        traspaso.concepto = 'Otro concepto'
        traspaso.clean_save()
        mock_saldo_save.assert_not_called()

    def test_integrativo_no_modifica_saldo_en_mov_si_no_se_modifica_importe_ni_cuentas_ni_fecha(
            self, traspaso):
        saldo_ce = traspaso.cta_entrada.saldo(traspaso)
        saldo_cs = traspaso.cta_salida.saldo(traspaso)

        traspaso.concepto = 'Depósito en efectivo'
        traspaso.clean_save()

        assert traspaso.cta_entrada.saldo(traspaso) == saldo_ce
        assert traspaso.cta_salida.saldo(traspaso) == saldo_cs


class TestSaveMovimientoEntreCuentasDeDistintosTitulares:
    def test_con_dos_cuentas_de_titulares_distintos_crea_dos_cuentas_credito(self, dia, credito_no_guardado):
        credito_no_guardado.clean_save()
        assert Cuenta.cantidad() == 4

        cc1 = list(Cuenta.todes())[-1]
        cc2 = list(Cuenta.todes())[-2]
        assert cc1.sk == '_otro-titular'
        assert cc2.sk == '_titular-otro'

    def test_si_no_se_pasa_dia_ni_fecha_crea_cuentas_credito_con_fecha_ultimo_dia(self, dia, dia_posterior, credito_no_guardado):
        credito_no_guardado.dia = None
        credito_no_guardado.clean_save()

        cc1 = list(Cuenta.todes())[-1]
        cc2 = list(Cuenta.todes())[-2]

        assert cc1.fecha_creacion == cc2.fecha_creacion == dia_posterior.fecha

    def test_con_dos_cuentas_de_titulares_distintos_guarda_cuentas_credito_como_contracuentas(
            self, dia, credito_no_guardado):
        credito_no_guardado.clean_save()
        cta_acreedora, cta_deudora = list(Cuenta.todes())[-2:]
        assert cta_acreedora.contracuenta == cta_deudora
        assert cta_deudora.contracuenta == cta_acreedora

    @pytest.mark.parametrize('campo_cuenta, fixt_cuenta', [
        ('cta_entrada', 'cuenta_ajena_2'),
        ('cta_salida', 'cuenta_2'),
    ])
    def test_cambiar_cuenta_por_cta_mismo_titular_de_cuenta_opuesta_en_movimiento_de_traspaso_con_contramovimiento_destruye_contramovimiento(
            self, credito, campo_cuenta, fixt_cuenta, request):
        cuenta = request.getfixturevalue(fixt_cuenta)
        id_contramovimiento = credito.id_contramov

        setattr(credito, campo_cuenta, cuenta)
        credito.clean_save()

        with pytest.raises(Movimiento.DoesNotExist):
            Movimiento.tomar(id=id_contramovimiento)

        assert credito.id_contramov is None

    @pytest.mark.parametrize('campo_cuenta, sk_ce, sk_cs', [
        ('cta_entrada', '_otro-gordo', '_gordo-otro'),
        ('cta_salida', '_gordo-titular', '_titular-gordo'),
    ])
    def test_cambiar_cuenta_de_movimiento_entre_titulares_por_cuenta_de_otro_titular_cambia_cuentas_en_contramovimiento(
            self, credito, campo_cuenta, sk_ce, sk_cs, titular_gordo, fecha):
        cuenta_gorda = Cuenta.crear(nombre="Cuenta gorda", sk="cg", titular=titular_gordo, fecha_creacion=fecha)
        setattr(credito, campo_cuenta, cuenta_gorda)
        credito.clean_save()

        assert Movimiento.tomar(id=credito.id_contramov).cta_entrada.sk == sk_ce
        assert Movimiento.tomar(id=credito.id_contramov).cta_salida.sk == sk_cs

    @pytest.mark.parametrize('campo_cuenta, fixt_cuenta', [
        ('cta_entrada', 'cuenta_2'),
        ('cta_salida', 'cuenta_ajena_2')
    ])
    def test_cambiar_cuenta_de_movimiento_entre_titulares_por_cuenta_del_mismo_titular_no_cambia_cuentas_en_contramovimiento(
            self, credito, campo_cuenta, fixt_cuenta, request):
        cuenta = request.getfixturevalue(fixt_cuenta)
        contramov = Movimiento.tomar(id=credito.id_contramov)
        ce_contramov = contramov.cta_entrada
        cs_contramov = contramov.cta_salida

        setattr(credito, campo_cuenta, cuenta)
        credito.clean_save()

        contramov = Movimiento.tomar(id=credito.id_contramov)
        assert contramov.cta_entrada == ce_contramov
        assert contramov.cta_salida == cs_contramov

    @pytest.mark.parametrize('campo,fixt', [
        ('importe', 'importe_aleatorio'),
        ('fecha', 'fecha_tardia'),
    ])
    def test_cambiar_campo_sensible_de_movimiento_entre_titulares_regenera_contramovimiento(
            self, credito, campo, fixt, request):
        valor = request.getfixturevalue(fixt)
        id_contramov = credito.id_contramov
        setattr(credito, campo, valor)
        credito.clean_save()
        assert credito.id_contramov != id_contramov

    def test_contramovimiento_regenerado_se_guarda_con_el_mismo_orden_dia_y_sk_que_tenia(self, credito):
        contramov = Movimiento.tomar(id=credito.id_contramov)
        credito.importe = credito.importe + 10
        credito.clean_save()
        contramov_regenerado = Movimiento.tomar(id=credito.id_contramov)
        assert contramov_regenerado.orden_dia == contramov.orden_dia
        assert contramov_regenerado.sk == contramov.sk

    @pytest.mark.parametrize('campo, valor', [
        ('concepto', 'otro concepto'),
        ('detalle', 'otro detalle'),
        ('orden_dia', 0)
    ])
    def test_cambiar_campo_no_sensible_de_movimiento_entre_titulares_no_regenera_contramovimiento(
            self, credito, campo, valor, request):
        id_contramov = credito.id_contramov
        setattr(credito, campo, valor)
        credito.clean_save()
        assert credito.id_contramov == id_contramov

    @pytest.mark.parametrize('campo,fixt', [
        ('importe', 'importe_aleatorio'),
        ('fecha', 'fecha_tardia'),
    ])
    def test_cambiar_campo_sensible_de_movimiento_entre_titulares_cambia_el_mismo_campo_en_contramovimiento(
            self, credito, campo, fixt, request):
        valor = request.getfixturevalue(fixt)
        setattr(credito, campo, valor)
        credito.clean_save()
        contramov = Movimiento.tomar(id=credito.id_contramov)
        assert getattr(contramov, campo) == valor

    class TestCambioEnTraspasoDeSaldoEntreDistintosTitulares:
        def test_permite_modificar_traspaso_de_saldo_de_cuenta_acumulativa_de_mas_de_un_titular(
                self, cuenta_de_dos_titulares):

            mov = cuenta_de_dos_titulares.movs().last()
            mov.concepto = "nuevo concepto"
            mov.clean_save()

            try:
                mov.clean_save()
            except AttributeError as e:
                raise AssertionError(
                    "No permite guardar modificación de movimiento de traspaso de saldo "
                    "de cuenta acumulativa con subcuentas de más de un titular. ",
                ) from e

        pass

        def test_si_se_cambia_subcuenta_por_subcuenta_del_mismo_titular_contramovimiento_es_igual_al_de_antes_del_cambio(
                self, cuenta_acumulativa_con_credito, titular_gordo):
            sc1, sc2 = cuenta_acumulativa_con_credito.subcuentas.all()
            sc3 = cuenta_acumulativa_con_credito.agregar_subcuenta(
                nombre="subcuenta de titular gordo",
                sk="sc3",
                titular=titular_gordo,
                fecha=cuenta_acumulativa_con_credito.fecha_conversion
            )
            mov = sc2.movs().first()
            contramov = Movimiento.tomar(pk=mov.id_contramov)
            data = model_to_dict(contramov, exclude=["id"])

            mov.cta_entrada = sc3
            mov.clean_save()
            contramov = Movimiento.tomar(pk=mov.id_contramov)
            new_data = model_to_dict(contramov, exclude=["id"])

            assert new_data == data

        def test_si_se_cambia_subcuenta_por_subcuenta_del_titular_de_la_otra_subcuenta_se_elimina_contramovimiento(
                self, cuenta_de_dos_titulares, otro_titular):
            sc1, sc2 = cuenta_de_dos_titulares.subcuentas.all()
            sc3 = cuenta_de_dos_titulares.agregar_subcuenta(
                nombre="subcuenta de titular gordo",
                sk="sc3",
                titular=otro_titular,
                fecha=cuenta_de_dos_titulares.fecha_conversion
            )
            mov = sc2.movs().first()

            mov.cta_entrada = sc3
            mov.clean_save()
            assert mov.id_contramov is None

        def test_si_se_cambia_subcuenta_por_subcuenta_de_un_tercer_titular_cambia_contramovimiento_por_otro_con_el_tercer_titular(
                self, cuenta_acumulativa_con_credito, titular):
            sc1, sc2 = cuenta_acumulativa_con_credito.subcuentas.all()
            sc3 = cuenta_acumulativa_con_credito.agregar_subcuenta(
                nombre="subcuenta de titular",
                sk="sc3",
                titular=titular,
                fecha=cuenta_acumulativa_con_credito.fecha_conversion
            )
            mov = sc2.movs().first()
            contramov = Movimiento.tomar(pk=mov.id_contramov)
            data = model_to_dict(contramov, exclude=["id", "detalle", "cta_entrada", "cta_salida"])

            mov.cta_entrada = sc3
            mov.clean_save()
            contramov = Movimiento.tomar(pk=mov.id_contramov)
            new_data = model_to_dict(contramov, exclude=["id", "detalle", "cta_entrada", "cta_salida"])
            t1 = sc3.titular
            t2 = cuenta_acumulativa_con_credito.titular_original

            assert new_data == data
            assert contramov.detalle == "Constitución de crédito"
            assert contramov.cta_entrada == Cuenta.tomar(sk=f"_{t2.sk}-{t1.sk}")
            assert contramov.cta_salida == Cuenta.tomar(sk=f"_{t1.sk}-{t2.sk}")


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaImporte:
    @pytest.mark.parametrize("otros_movs", [[], ["traspaso"]])
    def test_resta_importe_antiguo_y_suma_el_nuevo_a_saldo_diario(self, sentido, otros_movs, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        importe_mov = mov.importe_cta(sentido)
        importe_sd = saldo_diario.importe

        mov.importe += 50
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd + mov.importe_cta(sentido) - importe_mov

    @pytest.mark.parametrize("otros_movs", [
        [],
        ["entrada", "entrada_otra_cuenta"],
        ["entrada"],
        ["entrada_otra_cuenta"]
    ])
    def test_en_mov_de_traspaso_con_mas_movs_de_ambas_cuentas_en_el_dia_modifica_importe_de_ambos_saldos_diarios(
            self, traspaso, sentido, otros_movs, request):
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        cuenta = getattr(traspaso, f"cta_{sentido}")
        importe = traspaso.importe_cta(sentido)
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=traspaso.dia)
        importe_sd = saldo_diario.importe

        traspaso.importe += 50
        traspaso.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd - importe + traspaso.importe_cta(sentido)

    @pytest.mark.parametrize("otros_movs", [[], ["traspaso"]])
    def test_actualiza_saldos_diarios_posteriores_de_cuenta(self, sentido, otros_movs, salida_posterior, request):
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        mov = request.getfixturevalue(sentido)
        importe = mov.importe_cta(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
        importe_sdp = saldo_diario_posterior.importe

        mov.importe += 50
        mov.clean_save()

        saldo_diario_posterior.refresh_from_db()
        assert saldo_diario_posterior.importe == importe_sdp - importe + mov.importe_cta(sentido)

    @pytest.mark.parametrize("otros_movs", [[], ["Otro movimiento de crédito el mismo día"]])
    def test_en_movimiento_de_credito_resta_importe_viejo_y_suma_el_nuevo_a_saldo_diario_de_cuentas_contramov(
            self, credito, sentido, otros_movs):
        for otro_mov in otros_movs:
            Movimiento.crear(
                concepto=otro_mov,
                importe=120,
                cta_entrada=credito.cta_entrada,
                cta_salida=credito.cta_salida,
                dia=credito.dia
            )
        contramov = Movimiento.tomar(id=credito.id_contramov)
        cuenta_contramov = getattr(contramov, f"cta_{sentido}")
        importe_contramov = contramov.importe_cta(sentido)
        saldo_diario_contramov = SaldoDiario.tomar(cuenta=cuenta_contramov, dia=contramov.dia)
        importe_sdc = saldo_diario_contramov.importe

        credito.importe += 50
        credito.clean_save()

        contramov = Movimiento.tomar(id=credito.id_contramov)
        saldo_diario_contramov = SaldoDiario.tomar(cuenta=saldo_diario_contramov.cuenta, dia=saldo_diario_contramov.dia)
        assert \
            saldo_diario_contramov.importe == \
            importe_sdc - importe_contramov + contramov.importe_cta(sentido)


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaCuentas:
    def test_si_no_hay_mas_movs_de_cuenta_vieja_en_el_dia_elimina_su_saldo_diario(
            self, sentido, cuenta_2, request, mocker):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        mock_delete = mocker.patch("diario.models.movimiento.SaldoDiario.delete", autospec=True)

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.clean_save()

        mock_delete.assert_called_once_with(saldo_diario)

    def test_si_hay_mas_movs_de_cuenta_vieja_en_el_dia_resta_importe_de_su_saldo_diario(
            self, sentido, traspaso, cuenta_2, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        importe = saldo_diario.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe - mov.importe_cta(sentido)

    def test_si_no_hay_movs_de_cuenta_nueva_en_el_dia_crea_saldo_diario(self, sentido, cuenta_2, request, mocker):
        mov = request.getfixturevalue(sentido)
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.clean_save()

        mock_crear.assert_called_once_with(cuenta=cuenta_2, dia=mov.dia, importe=mov.importe_cta(sentido))

    def test_si_hay_movs_de_cuenta_nueva_en_el_dia_suma_importe_a_su_saldo_diario(
            self, sentido, traspaso, cuenta_2, request):
        mov = request.getfixturevalue(sentido)
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta_2, dia=mov.dia)
        importe = saldo_diario.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe + mov.importe_cta(sentido)

    def test_si_cta_cambia_de_sentido_en_dia_sin_mas_movimientos_de_la_cuenta_se_resta_importe_sentido_viejo_y_se_suma_importe_sentido_nuevo(
            self, sentido, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        importe_mov = mov.importe_cta(sentido)
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        importe_saldo_diario = saldo_diario.importe

        setattr(mov, f"cta_{sentido_opuesto}", cuenta)
        setattr(mov, f"cta_{sentido}", None)
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert \
            saldo_diario.importe == \
            importe_saldo_diario - importe_mov + mov.importe_cta(sentido_opuesto)

    def test_si_cta_cambia_de_sentido_en_dia_con_mas_movimientos_de_la_cuenta_se_resta_importe_sentido_viejo_y_se_suma_importe_sentido_nuevo(
            self, sentido, traspaso, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        importe_mov = mov.importe_cta(sentido)
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        importe_saldo_diario = saldo_diario.importe

        setattr(mov, f"cta_{sentido_opuesto}", cuenta)
        setattr(mov, f"cta_{sentido}", None)
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert \
            saldo_diario.importe == \
            importe_saldo_diario - importe_mov + mov.importe_cta(sentido_opuesto)

    def test_en_traspaso_en_dia_sin_mas_movimientos_de_la_cuenta_reemplazada_se_elimina_su_saldo_diario(
            self, sentido, traspaso, cuenta_3, mocker):
        cuenta = getattr(traspaso, f"cta_{sentido}")
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=traspaso.dia)
        mock_delete = mocker.patch("diario.models.movimiento.SaldoDiario.delete", autospec=True)

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        traspaso.clean_save()
        mock_delete.assert_called_once_with(saldo_diario)

    def test_en_traspaso_en_dia_con_mas_movimientos_de_la_cuenta_reemplazada_se_resta_importe_de_su_saldo_diario(
            self, sentido, traspaso, cuenta_3):
        cuenta = getattr(traspaso, f"cta_{sentido}")
        Movimiento.crear(f"Otro movimiento de {cuenta.nombre}", 200, cuenta, dia=traspaso.dia)
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=traspaso.dia)
        importe_sd = saldo_diario.importe

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        traspaso.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd - traspaso.importe_cta(sentido)

    def test_si_cambia_cuenta_en_traspaso_en_dia_sin_mas_movimientos_de_la_cuenta_reemplazante_se_crea_saldo_diario(
            self, sentido, traspaso, cuenta_3, mocker):
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        traspaso.clean_save()
        mock_crear.assert_called_once_with(cuenta=cuenta_3, dia=traspaso.dia, importe=traspaso.importe_cta(sentido))

    def test_si_cambia_cuenta_en_traspaso_en_dia_con_mas_movimientos_de_la_cuenta_reemplazante_se_suma_importe_a_su_saldo_diario(
            self, sentido, traspaso, cuenta_3):
        Movimiento.crear(f"Otro movimientod de cuenta_3", 200, cuenta_3, dia=traspaso.dia)
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta_3, dia=traspaso.dia)
        importe_sd = saldo_diario.importe

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        traspaso.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd + traspaso.importe_cta(sentido)

    def test_si_cambian_ambas_cuentas_en_traspaso_en_dia_sin_mas_movimientos_de_ninguna_de_las_cuentas_reemplazadas_se_eliminan_saldo_de_ambas_cuentas(
            self, sentido, traspaso, cuenta_3, cuenta_4, mocker):
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        cuenta = getattr(traspaso, f"cta_{sentido}")
        saldo_diario_cuenta = SaldoDiario.tomar(cuenta=cuenta, dia=traspaso.dia)
        cuenta_opuesta = getattr(traspaso, f"cta_{sentido_opuesto}")
        saldo_diario_cuenta_opuesta = SaldoDiario.tomar(cuenta=cuenta_opuesta, dia=traspaso.dia)
        mock_delete = mocker.patch("diario.models.movimiento.SaldoDiario.delete", autospec=True)

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        setattr(traspaso, f"cta_{sentido_opuesto}", cuenta_4)
        traspaso.clean_save()

        for saldo_diario in (saldo_diario_cuenta, saldo_diario_cuenta_opuesta):
            assert call(saldo_diario) in mock_delete.call_args_list

    def test_si_cambian_ambas_cuentas_en_traspaso_en_dia_con_mas_movimientos_de_una_de_las_cuentas_reemplazadas_se_resta_importe_del_saldo_diario_de_la_cuenta_con_otros_movimientos_y_se_elimina_el_saldo_diario_de_la_otra(
            self, sentido, traspaso, cuenta_3, cuenta_4, mocker):
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        cuenta = getattr(traspaso, f"cta_{sentido}")
        Movimiento.crear(f"Otro movimiento de {cuenta.nombre}", 200, cuenta, dia=traspaso.dia)
        saldo_diario_cuenta = SaldoDiario.tomar(cuenta=cuenta, dia=traspaso.dia)
        importe_sdc = saldo_diario_cuenta.importe
        cuenta_opuesta = getattr(traspaso, f"cta_{sentido_opuesto}")
        saldo_diario_cuenta_opuesta = SaldoDiario.tomar(cuenta=cuenta_opuesta, dia=traspaso.dia)
        mock_delete = mocker.patch("diario.models.movimiento.SaldoDiario.delete", autospec=True)

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        setattr(traspaso, f"cta_{sentido_opuesto}", cuenta_4)
        traspaso.clean_save()

        mock_delete.assert_called_once_with(saldo_diario_cuenta_opuesta)
        saldo_diario_cuenta.refresh_from_db()
        assert saldo_diario_cuenta.importe == importe_sdc - traspaso.importe_cta(sentido)

    def test_si_cambian_ambas_cuentas_en_traspaso_en_dia_con_mas_movimientos_de_ambas_cuentas_reemplazadas_se_resta_importe_de_saldo_diario_de_ambas_cuentas(
            self, sentido, traspaso, entrada, entrada_otra_cuenta, cuenta_3, cuenta_4):
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        cuenta = getattr(traspaso, f"cta_{sentido}")
        saldo_diario_cuenta = SaldoDiario.tomar(cuenta=cuenta, dia=traspaso.dia)
        importe_sdc = saldo_diario_cuenta.importe
        cuenta_opuesta = getattr(traspaso, f"cta_{sentido_opuesto}")
        saldo_diario_cuenta_opuesta = SaldoDiario.tomar(cuenta=cuenta_opuesta, dia=traspaso.dia)
        importe_sdco = saldo_diario_cuenta_opuesta.importe

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        setattr(traspaso, f"cta_{sentido_opuesto}", cuenta_4)
        traspaso.clean_save()

        saldo_diario_cuenta.refresh_from_db()
        assert saldo_diario_cuenta.importe == importe_sdc - traspaso.importe_cta(sentido)
        saldo_diario_cuenta_opuesta.refresh_from_db()
        assert \
            saldo_diario_cuenta_opuesta.importe == \
            importe_sdco - traspaso.importe_cta(sentido_opuesto)

    def test_si_cambian_ambas_cuentas_en_traspaso_en_dia_sin_mas_movimientos_de_ninguna_de_las_cuentas_reemplazantes_se_crean_saldos_diarios_para_ambas_cuentas(
            self, sentido, traspaso, cuenta_3, cuenta_4, mocker):
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        setattr(traspaso, f"cta_{sentido_opuesto}", cuenta_4)
        traspaso.clean_save()

        assert call(
            cuenta=cuenta_3,
            dia=traspaso.dia,
            importe=traspaso.importe_cta(sentido)
        ) in mock_crear.call_args_list
        assert call(
            cuenta=cuenta_4,
            dia=traspaso.dia,
            importe=traspaso.importe_cta(sentido_opuesto)
        ) in mock_crear.call_args_list

    def test_si_cambian_ambas_cuentas_en_traspaso_en_dia_con_mas_movimientos_de_una_de_las_cuentas_reemplazantes_se_suma_importe_al_saldo_diario_de_la_cuenta_con_otros_movimientos_y_se_crea_el_saldo_diario_de_la_otra(
            self, sentido, traspaso, cuenta_3, cuenta_4, mocker):
        Movimiento.crear("Otro movimiento de cuenta 3", 100, cuenta_3, dia=traspaso.dia)
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta_3, dia=traspaso.dia)
        importe_saldo_diario = saldo_diario.importe

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        setattr(traspaso, f"cta_{sentido_opuesto}", cuenta_4)
        traspaso.clean_save()

        mock_crear.assert_called_once_with(
            cuenta=cuenta_4,
            dia=traspaso.dia,
            importe=traspaso.importe_cta(sentido_opuesto)
        )
        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_saldo_diario + traspaso.importe_cta(sentido)

    def test_si_cambian_ambas_cuentas_en_traspaso_en_dia_con_mas_movimientos_de_ambas_cuentas_reemplazantes_se_suma_importe_a_saldo_diario_de_ambas_cuentas(
            self, sentido, traspaso, cuenta_3, cuenta_4):
        Movimiento.crear("Otro movimiento de cuenta 3", 100, cuenta_3, dia=traspaso.dia)
        Movimiento.crear("Otro movimiento de cuenta 4", 100, cuenta_4, dia=traspaso.dia)
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        saldo_diario_cta_3 = SaldoDiario.tomar(cuenta=cuenta_3, dia=traspaso.dia)
        saldo_diario_cta_4 = SaldoDiario.tomar(cuenta=cuenta_4, dia=traspaso.dia)
        importe_sdc3 = saldo_diario_cta_3.importe
        importe_sdc4 = saldo_diario_cta_4.importe

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        setattr(traspaso, f"cta_{sentido_opuesto}", cuenta_4)
        traspaso.clean_save()

        saldo_diario_cta_3.refresh_from_db()
        assert saldo_diario_cta_3.importe == importe_sdc3 + traspaso.importe_cta(sentido)
        saldo_diario_cta_4.refresh_from_db()
        assert saldo_diario_cta_4.importe == importe_sdc4 + traspaso.importe_cta(sentido_opuesto)

    def test_si_cambian_ambas_cuentas_en_traspaso_en_dia_sin_mas_movimientos_de_cuentas_reemplazadas_ni_reemplazantes_se_eliminan_saldos_diarios_de_cuentas_reemplazadas_y_se_crean_saldos_diarios_de_cuentas_reemplazantes(
            self, sentido, traspaso, cuenta_3, cuenta_4, mocker):
        """ Test redundante """
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        saldo_diario_cuenta = SaldoDiario.tomar(
            cuenta=getattr(traspaso, f"cta_{sentido}"),
            dia=traspaso.dia
        )
        saldo_diario_cuenta_opuesta = SaldoDiario.tomar(
            cuenta=getattr(traspaso, f"cta_{sentido_opuesto}"),
            dia=traspaso.dia
        )
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")
        mock_delete = mocker.patch("diario.models.movimiento.SaldoDiario.delete", autospec=True)

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        setattr(traspaso, f"cta_{sentido_opuesto}", cuenta_4)
        traspaso.clean_save()

        assert call(
            cuenta=cuenta_3,
            dia=traspaso.dia,
            importe=traspaso.importe_cta(sentido)
        ) in mock_crear.call_args_list
        assert call(
            cuenta=cuenta_4,
            dia=traspaso.dia,
            importe=traspaso.importe_cta(sentido_opuesto)
        ) in mock_crear.call_args_list
        assert call(saldo_diario_cuenta) in mock_delete.call_args_list
        assert call(saldo_diario_cuenta_opuesta) in mock_delete.call_args_list

    def test_si_cambian_ambas_cuentas_en_traspaso_en_dia_con_mas_movimientos_de_cuentas_reempazadas_y_reemplazantes_se_resta_importe_de_saldo_diario_de_cuentas_reemplazadas_y_se_suma_a_saldo_diario_de_cuentas_reemplazantes(
            self, sentido, traspaso, entrada, entrada_otra_cuenta, cuenta_3, cuenta_4):
        """ Test redundante """
        Movimiento.crear("Otro movimiento de cuenta 3", 100, cuenta_3, dia=traspaso.dia)
        Movimiento.crear("Otro movimiento de cuenta 4", 100, cuenta_4, dia=traspaso.dia)
        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        saldo_diario_cuenta = SaldoDiario.tomar(
            cuenta=getattr(traspaso, f"cta_{sentido}"),
            dia=traspaso.dia
        )
        saldo_diario_cuenta_opuesta = SaldoDiario.tomar(
            cuenta=getattr(traspaso, f"cta_{sentido_opuesto}"),
            dia=traspaso.dia
        )
        saldo_diario_cta_3 = SaldoDiario.tomar(cuenta=cuenta_3, dia=traspaso.dia)
        saldo_diario_cta_4 = SaldoDiario.tomar(cuenta=cuenta_4, dia=traspaso.dia)
        importe_sdc = saldo_diario_cuenta.importe
        importe_sdco = saldo_diario_cuenta_opuesta.importe
        importe_sdc3 = saldo_diario_cta_3.importe
        importe_sdc4 = saldo_diario_cta_4.importe

        setattr(traspaso, f"cta_{sentido}", cuenta_3)
        setattr(traspaso, f"cta_{sentido_opuesto}", cuenta_4)
        traspaso.clean_save()

        saldo_diario_cuenta.refresh_from_db()
        assert saldo_diario_cuenta.importe == importe_sdc - traspaso.importe_cta(sentido)
        saldo_diario_cuenta_opuesta.refresh_from_db()
        assert saldo_diario_cuenta_opuesta.importe == importe_sdco - traspaso.importe_cta(sentido_opuesto)
        saldo_diario_cta_3.refresh_from_db()
        assert saldo_diario_cta_3.importe == importe_sdc3 + traspaso.importe_cta(sentido)
        saldo_diario_cta_4.refresh_from_db()
        assert saldo_diario_cta_4.importe == importe_sdc4 + traspaso.importe_cta(sentido_opuesto)

    @pytest.mark.parametrize("otros_movs", [
        [],
        ["entrada", "entrada_otra_cuenta"],
        ["entrada"],
        ["entrada_otra_cuenta"]
    ])
    def test_si_se_intercambian_cuentas_en_traspaso_se_resta_importe_dos_veces_de_cta_que_pasa_a_salida_y_se_suma_dos_veces_a_cta_que_pasa_a_entrada(
            self, sentido, traspaso, otros_movs, request):
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)

        sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")
        cuenta = getattr(traspaso, f"cta_{sentido}")
        cuenta_opuesta = getattr(traspaso, f"cta_{sentido_opuesto}")
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=traspaso.dia)
        saldo_diario_opuesto = SaldoDiario.tomar(cuenta=cuenta_opuesta, dia=traspaso.dia)
        importe_sd = saldo_diario.importe
        importe_sdo = saldo_diario_opuesto.importe

        setattr(traspaso, f"cta_{sentido}", cuenta_opuesta)
        setattr(traspaso, f"cta_{sentido_opuesto}", cuenta)
        traspaso.clean_save()

        saldo_diario.refresh_from_db()
        assert \
            saldo_diario.importe == \
            importe_sd \
                - traspaso.importe_cta(sentido) \
                + traspaso.importe_cta(sentido_opuesto)

        saldo_diario_opuesto.refresh_from_db()
        assert \
            saldo_diario_opuesto.importe == \
            importe_sdo - \
                traspaso.importe_cta(sentido_opuesto) + \
                traspaso.importe_cta(sentido)

    @pytest.mark.parametrize("otros_movs", [[], ["traspaso"]])
    def test_resta_importe_de_saldos_diarios_posteriores_de_cuenta_vieja(
            self, sentido, cuenta_2, otros_movs, salida_posterior, request):
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        mov = request.getfixturevalue(sentido)
        cuenta= getattr(mov, f"cta_{sentido}")
        saldo_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
        importe_sp = saldo_posterior.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.clean_save()

        saldo_posterior.refresh_from_db()
        assert saldo_posterior.importe == importe_sp - mov.importe_cta(sentido)

    @pytest.mark.parametrize("otros_movs", [[], ["traspaso"]])
    def test_suma_importe_a_saldos_diarios_posteriores_de_cuenta_nueva(
            self, sentido, cuenta_2, otros_movs, entrada_posterior_otra_cuenta, request):
        mov = request.getfixturevalue(sentido)
        saldo_posterior = SaldoDiario.tomar(cuenta=cuenta_2, dia=entrada_posterior_otra_cuenta.dia)
        importe_sp = saldo_posterior.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.clean_save()

        saldo_posterior.refresh_from_db()
        assert saldo_posterior.importe == importe_sp + mov.importe_cta(sentido)

    def test_si_aparece_cuenta_de_otro_titular_en_movimiento_de_entrada_o_salida_se_genera_contramovimiento(
            self, sentido, cuenta_ajena, request):
        mov, s, _ = inferir_fixtures(sentido, request)
        campo_cuenta_vacio = 'cta_salida' if sentido == 'entrada' else 'cta_entrada'
        assert not mov.es_prestamo_o_devolucion()
        setattr(mov, campo_cuenta_vacio, cuenta_ajena)
        mov.clean_save()
        assert mov.es_prestamo_o_devolucion()

    def test_cambiar_cuenta_por_cuenta_de_otro_titular_en_movimientos_con_contramovimiento_regenera_contramovimiento(
            self, sentido, credito, cuenta_gorda, mocker):
        mock_regenerar_contramovimiento = mocker.patch(
            'diario.models.Movimiento._regenerar_contramovimiento',
            autospec=True
        )
        setattr(credito, f'cta_{sentido}', cuenta_gorda)
        credito.clean_save()

        mock_regenerar_contramovimiento.assert_called_once_with(credito)

    def test_cambiar_cuenta_por_cuenta_de_otro_titular_en_movimiento_de_traspaso_con_contramovimiento_modifica_contramovimiento(
            self, sentido, credito, cuenta_gorda):
        contramov = Movimiento.tomar(id=credito.id_contramov)
        contrasentido = 'entrada' if sentido == 'salida' else 'salida'
        cuenta_contramov = getattr(contramov, f'cta_{contrasentido}')

        setattr(credito, f'cta_{sentido}', cuenta_gorda)
        credito.clean_save()

        contramov = Movimiento.tomar(id=credito.id_contramov)
        assert getattr(contramov, f'cta_{contrasentido}').id != cuenta_contramov
        assert cuenta_gorda.titular.sk in getattr(contramov, f'cta_{contrasentido}').sk

    def test_cambiar_cuenta_por_cuenta_de_otro_titular_en_movimiento_de_traspaso_sin_contramovimiento_genera_contramovimiento(
            self, sentido, traspaso, cuenta_ajena, mocker):
        mock_crear_movimiento_credito = mocker.patch(
            'diario.models.Movimiento._crear_movimiento_credito',
            autospec=True
        )
        setattr(traspaso, f'cta_{sentido}', cuenta_ajena)
        traspaso.clean_save()

        mock_crear_movimiento_credito.assert_called_once_with(traspaso)

    def test_cambiar_cuenta_de_otro_titular_por_cuenta_del_mismo_titular_en_movimiento_de_traspaso_con_contramovimiento_destruye_contramovimiento_y_no_lo_regenera(
            self, sentido, credito, mocker, request):
        otra_cuenta = request.getfixturevalue("cuenta_ajena_2" if sentido == "entrada" else "cuenta_2")
        mock_eliminar_contramovimiento = mocker.patch(
            'diario.models.Movimiento._eliminar_contramovimiento',
            autospec=True
        )
        mock_crear_movimiento_credito = mocker.patch(
            'diario.models.Movimiento._crear_movimiento_credito'
        )

        setattr(credito, f'cta_{sentido}', otra_cuenta)
        credito.clean_save()

        mock_eliminar_contramovimiento.assert_called_once_with(credito)
        mock_crear_movimiento_credito.assert_not_called()

    class TestSaveCambiaCuentasBimonetario:
        # Cambia cuenta en moneda del movimiento no cambia cotización no cambia importe
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_una_tercera_moneda_se_recalculan_cotizacion_e_importe(
                self, sentido, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"
            moneda_otra_cuenta = getattr(movimiento, f"cta_{sentido_otra_cuenta}").moneda

            cotizacion = movimiento.cotizacion
            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.clean_save()

            assert \
                movimiento.cotizacion == \
                real.cotizacion_en_al(moneda_otra_cuenta, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == round(importe * cotizacion / movimiento.cotizacion, 2)
            assert abs(movimiento.importe_cta(sentido)) == movimiento.importe
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == round(movimiento.importe * movimiento.cotizacion, 2)

        # Cambia cuenta en moneda del movimiento cambia cotización no cambia importe
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_una_tercera_moneda_y_cotizacion_se_guarda_cotizacion_ingresada_y_se_recalcula_importe(
                self, sentido, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            importe = movimiento.importe
            cotizacion = movimiento.cotizacion

            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.cotizacion = 8
            movimiento.clean_save()

            assert movimiento.cotizacion == 8
            assert movimiento.importe == round(importe * cotizacion / 8, 2)
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == movimiento.importe * 8
            assert abs(movimiento.importe_cta(sentido)) == movimiento.importe

        # Cambia cuenta en moneda del movimiento cambia cotización cambia importe
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_tercera_moneda_cotizacion_e_importe_se_guardan_valores_ingresados(
                self, sentido, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.cotizacion = 8
            movimiento.importe = 5
            movimiento.clean_save()

            assert movimiento.cotizacion == 8
            assert movimiento.importe == 5
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == 5 * 8
            assert abs(movimiento.importe_cta(sentido)) == 5

        # Cambia cuenta en moneda del movimiento no cambia cotización cambia importe
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_tercera_moneda_e_importe_se_recalcula_cotizacion_y_se_guarda_importe_ingresado(
                self, sentido, cuenta_con_saldo_en_reales, real, euro, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.importe = 5
            movimiento.clean_save()

            assert \
                movimiento.cotizacion == real.cotizacion_en_al(euro, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 5
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == round(5 * movimiento.cotizacion, 2)
            assert abs(movimiento.importe_cta(sentido)) == 5

        # Cambia cuenta en otra moneda no cambia cotización no cambia importe
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_una_tercera_moneda_se_recalculan_cotizacion_e_importe(
                self, sentido, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            importe = movimiento.importe
            importe_cta_en_moneda_mov = movimiento.importe_cta(sentido)

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)

            assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda() is False
            assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) is True
            movimiento.clean_save()

            assert \
                movimiento.cotizacion == \
                movimiento.moneda.cotizacion_en_al(real, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == importe
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == round(importe * movimiento.cotizacion, 2)
            assert movimiento.importe_cta(sentido) == importe_cta_en_moneda_mov

        # Cambia cuenta en otra moneda cambia cotización no cambia importe
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_una_tercera_moneda_y_cotizacion_se_guarda_cotizacion_ingresada_y_se_recalcula_importe(
                self, sentido, cuenta_con_saldo_en_reales, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            importe = movimiento.importe
            importe_cuenta_en_mon_mov = movimiento.importe_cta(sentido)

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            movimiento.cotizacion = 0.2
            movimiento.clean_save()

            assert movimiento.cotizacion == 0.2
            assert movimiento.importe == importe
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == importe * 0.2
            assert movimiento.importe_cta(sentido) == importe_cuenta_en_mon_mov

        # Cambia cuenta en otra moneda cambia cotización cambia importe
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_una_tercera_moneda_cotizacion_e_importe_se_guardan_los_valores_ingresados(
                self, sentido, cuenta_con_saldo_en_reales, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            movimiento.cotizacion = 0.2
            movimiento.importe = 5
            movimiento.clean_save()

            assert movimiento.cotizacion == 0.2
            assert movimiento.importe == 5
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == 5 * 0.2
            assert abs(movimiento.importe_cta(sentido)) == 5

        # Cambia cuenta en otra moneda no cambia cotización cambia importe
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_una_tercera_moneda_e_importe_se_recalcula_cotizacion_y_se_guarda_importe_ingresado(
                self, sentido, cuenta_con_saldo_en_reales, real, dolar, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            movimiento.importe = 5
            movimiento.clean_save()

            assert \
                movimiento.cotizacion == \
                dolar.cotizacion_en_al(real, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 5
            assert \
                abs(movimiento.importe_cta(sentido_otra_cuenta)) == \
                round(5 * movimiento.cotizacion, 2)
            assert abs(movimiento.importe_cta(sentido)) == 5

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda no cambia cotización no cambia importe
        # Cambia moneda por moneda de cuenta que reemplaza a cuenta en moneda del movimiento
        def test_si_cambian_ambas_cuentas_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_moneda_del_movimiento_se_recalcula_cotizacion(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = yen
            movimiento.clean_save()

            assert \
                movimiento.cotizacion == \
                yen.cotizacion_en_al(real, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == importe
            assert \
                abs(movimiento.importe_cta(sentido_otra_cuenta)) == \
                round(movimiento.importe * movimiento.cotizacion, 2)
            assert abs(movimiento.importe_cta(sentido)) == movimiento.importe

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda no cambia cotización no cambia importe
        # Cambia moneda por moneda de cuenta que reemplaza a cuenta en otra moneda
        def test_si_cambian_ambas_cuentas_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_otra_moneda_se_recalcula_cotizacion(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido_otra_cuenta == "entrada"

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = real
            movimiento.clean_save()

            assert movimiento.cotizacion == real.cotizacion_en_al(yen, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == importe
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == movimiento.importe
            assert \
                abs(movimiento.importe_cta(sentido)) == \
                round(movimiento.importe * movimiento.cotizacion, 2)

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda no cambia cotización cambia importe
        # Cambia moneda por moneda de cuenta que reemplaza a cuenta en moneda del movimiento
        def test_si_cambian_ambas_cuentas_importe_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_moneda_del_movimiento_se_recalcula_cotizacion(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = yen
            movimiento.importe = 8
            movimiento.clean_save()

            assert movimiento.cotizacion == yen.cotizacion_en_al(real, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 8
            assert \
                abs(movimiento.importe_cta(sentido_otra_cuenta)) == \
                round(movimiento.importe * movimiento.cotizacion, 2)
            assert abs(movimiento.importe_cta(sentido)) == 8

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda no cambia cotización cambia importe
        # Cambia moneda por moneda de cuenta que reemplaza a cuenta en otra moneda
        def test_si_cambian_ambas_cuentas_importe_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_otra_moneda_se_recalcula_cotizacion(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido_otra_cuenta == "entrada"

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = real
            movimiento.importe = 8
            movimiento.clean_save()

            assert movimiento.cotizacion == real.cotizacion_en_al(yen, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 8
            assert \
                abs(movimiento.importe_cta(sentido)) == \
                round(movimiento.importe * movimiento.cotizacion, 2)
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == 8

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda cambia cotización no cambia importe
        # Cambia moneda por moneda de cuenta que reemplaza a cuenta en moneda del movimiento
        def test_si_cambian_ambas_cuentas_cotizacion_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_moneda_del_movimiento_no_se_recalcula_importe(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = yen
            movimiento.cotizacion = 3
            movimiento.clean_save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == importe
            assert \
                abs(movimiento.importe_cta(sentido_otra_cuenta)) == \
                movimiento.importe * 3
            assert abs(movimiento.importe_cta(sentido)) == movimiento.importe

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda cambia cotización no cambia importe
        # Cambia moneda por moneda que reemplaza a cuenta en otra moneda
        def test_si_cambian_ambas_cuentas_cotizacion_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_otra_moneda_no_se_recalcula_importe(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = real
            movimiento.cotizacion = 3
            movimiento.clean_save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == importe
            assert \
                abs(movimiento.importe_cta(sentido)) == \
                movimiento.importe * 3
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == movimiento.importe

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda cambia cotización cambia importe
        # Cambia moneda por moneda que reemplaza a cuenta en moneda del movimiento
        def test_si_cambian_ambas_cuentas_cotizacion_importe_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_moneda_del_movimiento_se_guardan_valores_ingresados(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = yen
            movimiento.cotizacion = 3
            movimiento.importe = 8
            movimiento.clean_save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == 8
            assert \
                abs(movimiento.importe_cta(sentido_otra_cuenta)) == \
                movimiento.importe * 3
            assert abs(movimiento.importe_cta(sentido)) == movimiento.importe

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda cambia cotización cambia importe
        # Cambia moneda por moneda que reemplaza a cuenta en otra moneda
        def test_si_cambian_ambas_cuentas_cotizacion_importe_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_otra_moneda_se_guardan_valores_ingresados(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = real
            movimiento.cotizacion = 3
            movimiento.importe = 8
            movimiento.clean_save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == 8
            assert abs(movimiento.importe_cta(sentido)) == movimiento.importe * 3
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == movimiento.importe

        def test_si_cambian_ambas_cuentas_cotizacion_e_importe_se_guardan_valores_ingresados(
                self, sentido, cuenta_con_saldo_en_yenes, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_yenes)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.cotizacion = 3
            movimiento.importe = 8
            movimiento.clean_save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == 8
            assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == 8 * 3
            assert abs(movimiento.importe_cta(sentido)) == 8

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # no cambia moneda, no cambia cotización, no cambia importe
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_se_calcula_cotizacion(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            importe = traspaso_en_dolares.importe
            compra = sentido_otra_cuenta == "entrada"

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.clean_save()

            assert \
                traspaso_en_dolares.cotizacion == \
                dolar.cotizacion_en_al(euro, fecha=traspaso_en_dolares.fecha, compra=compra)
            assert traspaso_en_dolares.importe == importe
            assert \
                abs(traspaso_en_dolares.importe_cta(sentido_otra_cuenta)) == \
                traspaso_en_dolares.importe
            assert \
                abs(traspaso_en_dolares.importe_cta(sentido)) == \
                round(traspaso_en_dolares.importe * traspaso_en_dolares.cotizacion, 2)

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # no cambia moneda, cambia cotización, no cambia importe
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_y_cotizacion_se_guarda_cotizacion(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            importe = traspaso_en_dolares.importe

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.cotizacion = 2
            traspaso_en_dolares.clean_save()

            assert traspaso_en_dolares.cotizacion == 2
            assert traspaso_en_dolares.importe == importe
            assert abs(traspaso_en_dolares.importe_cta(sentido_otra_cuenta)) == traspaso_en_dolares.importe
            assert \
                abs(traspaso_en_dolares.importe_cta(sentido)) == \
                traspaso_en_dolares.importe * 2

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # cambia moneda, no cambia cotización, no cambia importe
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_y_moneda_se_calcula_cotizacion_e_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"
            importe = traspaso_en_dolares.importe

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.moneda = euro
            traspaso_en_dolares.clean_save()

            assert \
                traspaso_en_dolares.cotizacion == \
                euro.cotizacion_en_al(dolar, fecha=traspaso_en_dolares.fecha, compra=compra)
            assert traspaso_en_dolares.importe == round(importe / traspaso_en_dolares.cotizacion, 2)
            assert abs(traspaso_en_dolares.importe_cta(sentido)) == traspaso_en_dolares.importe
            assert abs(traspaso_en_dolares.importe_cta(sentido_otra_cuenta)) == importe

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # no cambia moneda, no cambia cotización, cambia importe
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_e_importe_se_calcula_cotizacion_y_se_guarda_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido_otra_cuenta == "entrada"

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.importe = 6
            traspaso_en_dolares.clean_save()

            assert \
                traspaso_en_dolares.cotizacion == \
                dolar.cotizacion_en_al(euro, fecha=traspaso_en_dolares.fecha, compra=compra)
            assert traspaso_en_dolares.importe == 6
            assert \
                abs(traspaso_en_dolares.importe_cta(sentido)) == \
                round(6 * traspaso_en_dolares.cotizacion, 2)
            assert abs(traspaso_en_dolares.importe_cta(sentido_otra_cuenta)) == 6

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # cambia moneda, cambia cotización, no cambia importe
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_moneda_y_cotizacion_se_guarda_cotizacion_y_se_calcula_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            importe = traspaso_en_dolares.importe

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.cotizacion = 2
            traspaso_en_dolares.moneda = euro
            traspaso_en_dolares.clean_save()

            assert traspaso_en_dolares.cotizacion == 2
            assert traspaso_en_dolares.importe == importe / 2
            assert \
                abs(traspaso_en_dolares.importe_cta(sentido)) == traspaso_en_dolares.importe
            assert abs(traspaso_en_dolares.importe_cta(sentido_otra_cuenta)) == importe

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # cambia moneda, no cambia cotización, cambia importe
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_moneda_e_importe_se_calcula_cotizacion_y_se_guarda_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.importe = 6
            traspaso_en_dolares.moneda = euro
            traspaso_en_dolares.clean_save()

            assert \
                traspaso_en_dolares.cotizacion == \
                euro.cotizacion_en_al(dolar, fecha=traspaso_en_dolares.fecha, compra=compra)
            assert traspaso_en_dolares.importe == 6
            assert \
                abs(traspaso_en_dolares.importe_cta(sentido)) == 6
            assert \
                abs(traspaso_en_dolares.importe_cta(sentido_otra_cuenta)) == \
                round(6 * traspaso_en_dolares.cotizacion, 2)

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # no cambia moneda, cambia cotización, cambia importe
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_cotizacion_e_importe_se_guardan_cotizacion_e_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.importe = 6
            traspaso_en_dolares.cotizacion = 0.6
            traspaso_en_dolares.clean_save()

            assert traspaso_en_dolares.cotizacion == 0.6
            assert traspaso_en_dolares.importe == 6
            assert \
                abs(traspaso_en_dolares.importe_cta(sentido)) == round(6 * 0.6, 2)
            assert abs(traspaso_en_dolares.importe_cta(sentido_otra_cuenta)) == 6

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # cambia moneda, cambia cotización, cambia importe
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_moneda_cotizacion_e_importe_se_guardan_cotizacion_e_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.importe = 6
            traspaso_en_dolares.cotizacion = 0.6
            traspaso_en_dolares.moneda = euro
            traspaso_en_dolares.clean_save()

            assert traspaso_en_dolares.cotizacion == 0.6
            assert traspaso_en_dolares.importe == 6
            assert \
                abs(traspaso_en_dolares.importe_cta(sentido)) == 6
            assert abs(traspaso_en_dolares.importe_cta(sentido_otra_cuenta)) == round(6 * 0.6, 2)

        # Entre cuentas en distinta moneda, cambia cuenta en otra moneda por cuenta en moneda del movimiento,
        # no cambia importe
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_moneda_del_movimiento_cotizacion_pasa_a_1(
                self, sentido, cuenta_en_dolares, request):
            mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            importe = mov_distintas_monedas.importe

            setattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}", cuenta_en_dolares)
            mov_distintas_monedas.clean_save()

            assert mov_distintas_monedas.cotizacion == 1
            assert mov_distintas_monedas.importe == importe
            assert mov_distintas_monedas.importe_cta_entrada == mov_distintas_monedas.importe
            assert mov_distintas_monedas.importe_cta_salida == -mov_distintas_monedas.importe

        # Entre cuentas en distinta moneda, cambia cuenta en otra moneda por cuenta en moneda del movimiento,
        # cambia importe
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_moneda_del_movimiento_e_importe_se_guarda_importe_y_cotizacion_pasa_a_1(
                self, sentido, cuenta_en_dolares, request):
            mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}", cuenta_en_dolares)
            mov_distintas_monedas.importe = 6
            mov_distintas_monedas.clean_save()

            assert mov_distintas_monedas.cotizacion == 1
            assert mov_distintas_monedas.importe == 6
            assert mov_distintas_monedas.importe_cta_entrada == 6
            assert mov_distintas_monedas.importe_cta_salida == -6

        # Entre cuentas en distinta moneda, cambia cuenta en moneda del movimiento por cuenta en otra moneda,
        # no cambia importe
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_moneda_no_del_movimiento_se_calcula_importe_y_cotizacion_pasa_a_1(
                self, sentido, cuenta_en_euros, euro, request):
            mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            cotizacion = mov_distintas_monedas.cotizacion
            importe = mov_distintas_monedas.importe

            setattr(mov_distintas_monedas, f"cta_{sentido}", cuenta_en_euros)
            mov_distintas_monedas.moneda = euro
            mov_distintas_monedas.clean_save()

            assert mov_distintas_monedas.cotizacion == 1
            assert mov_distintas_monedas.importe == round(importe * cotizacion, 2)
            assert mov_distintas_monedas.importe_cta_entrada == mov_distintas_monedas.importe
            assert mov_distintas_monedas.importe_cta_salida == -mov_distintas_monedas.importe

        # Entre cuentas en distinta moneda, cambia cuenta en moneda del movimiento por cuenta en otra moneda,
        # cambia importe
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_moneda_no_del_movimiento_e_importe_se_guarda_importe_y_cotizacion_pasa_a_1(
                self, sentido, cuenta_en_euros, euro, request):
            mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")

            setattr(mov_distintas_monedas, f"cta_{sentido}", cuenta_en_euros)
            mov_distintas_monedas.moneda = euro
            mov_distintas_monedas.importe = 6
            mov_distintas_monedas.clean_save()

            assert mov_distintas_monedas.cotizacion == 1
            assert mov_distintas_monedas.importe == 6
            assert mov_distintas_monedas.importe_cta_entrada == 6
            assert mov_distintas_monedas.importe_cta_salida == -6

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # no cambia moneda, no cambia cotización, no cambia importe.
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_se_calcula_cotizacion(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.clean_save()

            assert \
                movimiento.cotizacion == \
                dolar.cotizacion_en_al(euro, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == importe
            assert abs(movimiento.importe_cta(sentido)) == importe
            assert \
                abs(movimiento.importe_cta(sentido_contracuenta)) == \
                round(importe * movimiento.cotizacion, 2)

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # no cambia moneda, cambia cotización, no cambia importe.
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cotizacion_se_guarda_cotizacion_ingresada(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.cotizacion = 1.5
            movimiento.clean_save()

            assert movimiento.cotizacion == 1.5
            assert movimiento.importe == importe
            assert abs(movimiento.importe_cta(sentido)) == importe
            assert abs(movimiento.importe_cta(sentido_contracuenta)) == round(importe * 1.5, 2)

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # no cambia moneda, no cambia cotización, cambia importe.
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_se_ingresa_importe_se_calcula_cotizacion_y_se_guarda_importe_ingresado(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.importe = 20
            movimiento.clean_save()

            assert \
                movimiento.cotizacion == \
                dolar.cotizacion_en_al(euro, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 20
            assert abs(movimiento.importe_cta(sentido)) == 20
            assert abs(movimiento.importe_cta(sentido_contracuenta)) == round(20 * movimiento.cotizacion, 2)

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # no cambia moneda, cambia cotización, cambia importe.
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_se_ingresa_cotizacion_e_importe_se_guardan_valores_ingresados(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.cotizacion = 1.5
            movimiento.importe = 20
            movimiento.clean_save()

            assert movimiento.cotizacion == 1.5
            assert movimiento.importe == 20
            assert abs(movimiento.importe_cta(sentido)) == 20
            assert abs(movimiento.importe_cta(sentido_contracuenta)) == 20 * 1.5

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # cambia moneda, no cambia cotización, no cambia importe.
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cambia_moneda_se_calcula_cotizacion_e_importe(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido_contracuenta == "entrada"

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.moneda = euro
            movimiento.clean_save()

            assert \
                movimiento.cotizacion == \
                euro.cotizacion_en_al(dolar, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == round(importe / movimiento.cotizacion, 2)
            assert \
                abs(movimiento.importe_cta(sentido)) == \
                round(movimiento.importe * movimiento.cotizacion, 2)
            assert abs(movimiento.importe_cta(sentido_contracuenta)) == movimiento.importe

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # cambia moneda, cambia cotización, no cambia importe.
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cambia_moneda_y_cotizacion_se_guarda_cotizacion_y_se_calcula_importe(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.moneda = euro
            movimiento.cotizacion = 0.8
            movimiento.clean_save()

            assert movimiento.cotizacion == 0.8
            assert movimiento.importe == round(importe / 0.8, 2)
            assert abs(movimiento.importe_cta(sentido)) == importe
            assert abs(movimiento.importe_cta(sentido_contracuenta)) == movimiento.importe

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # cambia moneda, no cambia cotización, cambia importe.
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cambia_moneda_e_importe_se_calcula_cotizacion_y_se_guarda_importe(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido_contracuenta == "entrada"

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.moneda = euro
            movimiento.importe = 20
            movimiento.clean_save()

            assert \
                movimiento.cotizacion == \
                euro.cotizacion_en_al(dolar, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 20
            assert abs(movimiento.importe_cta(sentido)) == round(20 * movimiento.cotizacion, 2)
            assert abs(movimiento.importe_cta(sentido_contracuenta)) == 20

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # cambia moneda, cambia cotización, cambia importe.
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cambia_moneda_cotizacion_e_importe_se_guardan_cotizacion_e_importe(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.moneda = euro
            movimiento.cotizacion = 0.8
            movimiento.importe = 20
            movimiento.clean_save()

            assert movimiento.cotizacion == 0.8
            assert movimiento.importe == 20
            assert abs(movimiento.importe_cta(sentido)) == round(20 * 0.8, 2)
            assert abs(movimiento.importe_cta(sentido_contracuenta)) == 20

        def test_puede_agregarse_cuenta_interactiva_a_movimiento_con_cta_acumulativa(
                self, sentido, cuenta_2, request):
            mov = request.getfixturevalue(f'{sentido}_con_ca')
            contrasentido = 'entrada' if sentido == 'salida' else 'salida'

            setattr(mov, f'cta_{contrasentido}', cuenta_2)
            mov.clean_save()

            assert getattr(mov, f'cta_{contrasentido}') == cuenta_2

        def test_puede_cambiarse_cta_interactiva_en_movimiento_con_cuenta_acumulativa(
                self, sentido, cuenta_3, request):
            mov = request.getfixturevalue(f'traspaso_con_cta_{sentido}_a')
            contrasentido = 'entrada' if sentido == 'salida' else 'salida'

            setattr(mov, f'cta_{contrasentido}', cuenta_3)
            mov.clean_save()

            assert getattr(mov, f'cta_{contrasentido}') == cuenta_3

        def test_puede_retirarse_cta_interactiva_en_movimiento_con_cta_entrada_acumulativa(
                self, sentido, request):
            mov = request.getfixturevalue(f'traspaso_con_cta_{sentido}_a')
            contrasentido = 'entrada' if sentido == 'salida' else 'salida'

            setattr(mov, f'cta_{contrasentido}', None)
            mov.clean_save()

            assert getattr(mov, f'cta_{contrasentido}') is None


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaImporteYCuentas:
    def test_si_cambia_cuenta_e_importe_en_dia_sin_mas_movimientos_de_la_cuenta_reemplazada_elimina_su_saldo_diario(
            self, sentido, cuenta_2, request, mocker):
        mov = request.getfixturevalue(sentido)
        mock_delete = mocker.patch("diario.models.movimiento.SaldoDiario.delete", autospec=True)

        cuenta = getattr(mov, f"cta_{sentido}")
        importe_viejo = mov.importe_cta(sentido)
        importe_nuevo = importe_viejo + 100
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.importe = importe_nuevo
        mov.clean_save()

        mock_delete.assert_called_once_with(saldo_diario)

    def test_si_cambia_cuenta_e_importe_en_dia_con_mas_movimientos_de_la_cuenta_reemplazada_resta_importe_viejo_de_su_saldo_diario(
            self, sentido, cuenta_2, traspaso, request):
        mov = request.getfixturevalue(sentido)

        cuenta = getattr(mov, f"cta_{sentido}")
        importe_viejo = mov.importe_cta(sentido)
        importe_nuevo = importe_viejo + 100
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        importe_sd = saldo_diario.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.importe = importe_nuevo
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd - importe_viejo

    def test_si_cambia_cuenta_e_importe_en_dia_sin_movimientos_de_la_cuenta_reemplazante_crea_saldo_diario_con_nuevo_importe(
            self, sentido, cuenta_2, request, mocker):
        mov = request.getfixturevalue(sentido)
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")

        importe_viejo = mov.importe_cta(sentido)
        importe_nuevo = importe_viejo + 100

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.importe = importe_nuevo
        mov.clean_save()

        mock_crear.assert_called_once_with(
            cuenta=cuenta_2,
            dia=mov.dia,
            importe=mov.importe_cta(sentido)
        )

    def test_si_cambia_cuenta_e_importe_en_dia_con_movimientos_de_la_cuenta_reemplazante_suma_importe_nuevo_a_su_saldo(
            self, sentido, traspaso, cuenta_2, request):
        mov = request.getfixturevalue(sentido)
        importe_nuevo = mov.importe + 100
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta_2, dia=mov.dia)
        importe_sd = saldo_diario.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.importe = importe_nuevo
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd + mov.importe_cta(sentido)


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaFecha:

    @pytest.mark.parametrize("otros_movs", [[], ["traspaso"]])
    def test_si_cambia_dia_a_dia_posterior_en_mov_unico_de_cuenta_en_el_dia_resta_importe_a_saldo_de_cuenta_en_el_dia(
            self, entrada_anterior, sentido, otros_movs, dia_posterior, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        saldo_diario = SaldoDiario.tomar(cuenta=getattr(mov, f"cta_{sentido}"), dia=mov.dia)
        importe_sd = saldo_diario.importe

        mov.dia = dia_posterior
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd - mov.importe_cta(sentido)
        if otros_movs == []:
            assert saldo_diario.importe == saldo_diario.anterior().importe

    def test_si_cambia_dia_a_dia_posterior_resta_importe_a_saldos_diarios_intermedios_de_cuenta_entre_dia_antiguo_y_dia_nuevo(
            self, sentido, salida_posterior, entrada_tardia, dia_tardio, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_intermedio = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
        importe_si = saldo_intermedio.importe

        mov.dia = dia_tardio
        mov.clean_save()

        saldo_intermedio.refresh_from_db()
        assert saldo_intermedio.importe == importe_si - mov.importe_cta(sentido)

    def test_si_cambia_dia_a_dia_posterior_sin_movimientos_de_cuenta_crea_saldo_diario_de_cuenta_en_el_nuevo_dia(
            self, sentido, dia_posterior, request, mocker):
        mov = request.getfixturevalue(sentido)
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")
        cuenta = getattr(mov, f"cta_{sentido}")

        mov.dia = dia_posterior
        mov.clean_save()

        mock_crear.assert_called_once_with(
            cuenta=cuenta,
            dia=dia_posterior,
            importe=mov.importe_cta(sentido)
        )

    @pytest.mark.parametrize("otros_movs", [[], ["salida_posterior"]])
    def test_si_cambia_dia_a_dia_posterior_no_modifica_saldos_diarios_posteriores_al_nuevo_dia(
            self, sentido, entrada_tardia, otros_movs, dia_posterior, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_tardio = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_tardia.dia)
        importe_st = saldo_tardio.importe

        mov.dia = dia_posterior
        mov.clean_save()

        saldo_tardio.refresh_from_db()
        assert saldo_tardio.importe == importe_st

    def test_si_cambia_dia_a_dia_posterior_con_movimientos_de_cuenta_no_modifica_saldo_diario_de_cuenta_en_el_nuevo_dia(
            self, sentido, salida_posterior, entrada_tardia, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
        importe_sp = saldo_posterior.importe

        mov.dia = salida_posterior.dia
        mov.clean_save()

        saldo_posterior.refresh_from_db()
        assert saldo_posterior.importe == importe_sp

    @pytest.mark.parametrize("otros_mov", [[], ["traspaso"]])
    def test_si_cambia_dia_a_dia_anterior_no_modifica_importe_del_saldo_diario_del_dia_viejo(
            self, sentido, otros_mov, dia_anterior, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_mov:
            request.getfixturevalue(otro_mov)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        importe_sd = saldo_diario.importe

        mov.dia = dia_anterior
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd

    def test_si_cambia_dia_a_dia_anterior_sin_movs_de_la_cuenta_crea_saldo_diario_de_cuenta(
            self, sentido, dia_anterior, request, mocker):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")

        mov.dia = dia_anterior
        mov.clean_save()

        mock_crear.assert_called_once_with(
            cuenta=cuenta,
            dia=dia_anterior,
            importe=mov.importe_cta(sentido)
        )

    def test_si_cambia_dia_a_dia_anterior_con_movs_de_la_cuenta_suma_importe_del_movimiento_a_saldo_diario_del_dia_nuevo(
            self, sentido, entrada_anterior, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario_anterior = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_anterior.dia)
        importe_sda = saldo_diario_anterior.importe

        mov.dia = entrada_anterior.dia
        mov.clean_save()

        saldo_diario_anterior.refresh_from_db()
        assert saldo_diario_anterior.importe == importe_sda + mov.importe_cta(sentido)

    @pytest.mark.parametrize("otros_movs", [[], ["entrada_temprana"]])
    def test_si_cambia_dia_a_dia_anterior_suma_importe_del_movimiento_a_saldos_intermedios_entre_el_dia_nuevo_y_el_viejo(
            self, sentido, dia_temprano, otros_movs, entrada_anterior, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario_intermedio = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_anterior.dia)
        importe_sdi = saldo_diario_intermedio.importe

        mov.dia = dia_temprano
        mov.clean_save()

        saldo_diario_intermedio.refresh_from_db()
        assert saldo_diario_intermedio.importe == importe_sdi + mov.importe_cta(sentido)

    @pytest.mark.parametrize("otros_movs", [[], ["entrada_anterior"]])
    def test_si_cambia_dia_a_dia_anterior_sin_movs_de_la_cuenta_no_modifica_importe_de_saldos_diarios_posteriores_a_dia_viejo(
            self, sentido, dia_anterior, otros_movs, salida_posterior, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
        importe_sdp = saldo_diario_posterior.importe

        mov.dia = dia_anterior
        mov.clean_save()

        saldo_diario_posterior.refresh_from_db()
        assert saldo_diario_posterior.importe == importe_sdp

    @pytest.mark.parametrize("otros_movs", [[], ["entrada_anterior"]])
    def test_si_cambia_dia_a_dia_anterior_no_modifica_importe_de_saldos_diarios_anteriores_a_dia_nuevo(
            self, sentido, dia_anterior, otros_movs, entrada_temprana, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario_temprano = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_temprana.dia)
        importe_sdt = saldo_diario_temprano.importe

        mov.dia = dia_anterior
        mov.clean_save()

        saldo_diario_temprano.refresh_from_db()
        assert saldo_diario_temprano.importe == importe_sdt

    def test_si_cambia_fecha_a_fecha_posterior_toma_primer_orden_dia_de_nueva_fecha(
            self, sentido, importe, salida_posterior, fecha_posterior, request):
        mov_ant, _, cuenta = inferir_fixtures(sentido, request)
        mov = Movimiento.crear('segundo del día', importe, cuenta, fecha=mov_ant.fecha)
        assert mov.orden_dia == 1

        cambiar_fecha(mov, fecha_posterior)

        assert mov.orden_dia == 0

    def test_si_cambia_fecha_a_fecha_posterior_movimientos_existentes_en_nuevo_dia_aumentan_su_orden_dia(
            self, sentido, importe, salida_posterior, fecha_posterior, request):
        mov_ant, _, cuenta = inferir_fixtures(sentido, request)
        mov = Movimiento.crear('segundo del día', importe, cuenta, fecha=mov_ant.fecha)
        assert salida_posterior.orden_dia == 0

        cambiar_fecha(mov, fecha_posterior)

        salida_posterior.refresh_from_db()
        assert salida_posterior.orden_dia == 1

    def test_si_cambia_fecha_a_fecha_anterior_toma_ultimo_orden_dia_de_nueva_fecha(
            self, sentido, entrada_anterior, fecha_anterior, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        assert mov.orden_dia == 0

        cambiar_fecha(mov, fecha_anterior)

        assert mov.orden_dia == 1

    def test_si_cambia_fecha_a_fecha_anterior_no_modifica_orden_dia_de_movimientos_existentes_en_el_nuevo_dia(
            self, sentido, entrada_anterior, fecha_anterior, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        orden_dia_otro_mov = entrada_anterior.orden_dia

        cambiar_fecha(mov, fecha_anterior)

        entrada_anterior.refresh_from_db()
        assert entrada_anterior.orden_dia == orden_dia_otro_mov

    def test_si_cambia_fecha_a_fecha_posterior_resta_importe_a_saldos_intermedios_de_cuenta_entre_antigua_y_nueva_posicion_de_movimiento(
            self, sentido, salida_posterior, entrada_tardia, fecha_tardia, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_intermedio = cuenta.saldo(salida_posterior)

        cambiar_fecha(mov, fecha_tardia)

        assert cuenta.saldo(salida_posterior) == saldo_intermedio - s * mov.importe


class TestSaveCambiaFechaConCtaAcumulativa:

    def test_modifica_fecha_en_movimiento_con_cuenta_acumulativa(
            self, traspaso, cuenta, fecha, fecha_posterior, fecha_tardia):
        dividir_en_dos_subcuentas(cuenta, fecha=fecha_tardia)
        traspaso.refresh_from_db()

        cambiar_fecha(traspaso, fecha_posterior)

        assert traspaso.cta_entrada.es_acumulativa
        assert not traspaso.cta_salida.es_acumulativa
        assert traspaso.fecha == fecha_posterior

    def test_permite_modificar_fecha_de_movimiento_de_traspaso_de_saldo_de_cuenta_acumulativa_por_fecha_posterior(
            self, cuenta, fecha, fecha_posterior):
        subc1, subc2 = cuenta.dividir_entre(
            ['subc1', 'sc1', 10],
            ['subc2', 'sc2'],
            fecha=fecha,
        )
        mov1 = Movimiento.tomar(cta_entrada=subc1)

        cambiar_fecha(mov1, fecha_posterior)

        assert mov1.fecha == fecha_posterior

    def test_si_se_modifica_fecha_de_un_movimiento_de_traspaso_de_saldo_se_modifica_fecha_de_conversion_de_cuenta_y_de_los_movimientos_restantes_de_traspaso_de_saldo(
            self, cuenta_con_saldo, fecha, fecha_posterior):
        subc1, subc2, subc3 = cuenta_con_saldo.dividir_entre(
            ['subc1', 'sc1', 10],
            ['subc2', 'sc2', 5],
            ['subc3', 'sc3'],
            fecha=fecha,
        )
        mov1 = Movimiento.tomar(cta_entrada=subc1)
        cambiar_fecha(mov1, fecha_posterior)

        cuenta = cuenta_con_saldo.tomar_del_sk()
        mov2 = Movimiento.tomar(cta_entrada=subc2)
        mov3 = Movimiento.tomar(cta_entrada=subc3)

        assert cuenta.fecha_conversion == fecha_posterior
        assert mov2.fecha == fecha_posterior
        assert mov3.fecha == fecha_posterior

    def test_funciona_si_se_modifica_movimiento_de_traspaso_con_cuentas_invertidas(
            self, cuenta, fecha, fecha_posterior):
        subc1, subc2 = cuenta.dividir_entre(
            ['subc1', 'sc1', 10],
            ['subc2', 'sc2'],
            fecha=fecha
        )
        mov2 = Movimiento.tomar(cta_salida=subc2)
        cambiar_fecha(mov2, fecha_posterior)

        cuenta = cuenta.tomar_del_sk()
        mov1 = Movimiento.tomar(cta_entrada=subc1)

        assert cuenta.fecha_conversion == fecha_posterior
        assert mov1.fecha == fecha_posterior


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaImporteYFecha:
    def test_si_cambia_importe_y_fecha_por_fecha_posterior_resta_importe_viejo_a_saldos_diarios_intermedios(
            self, sentido, salida_posterior, dia_tardio, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        importe_mov = mov.importe_cta(sentido)
        saldo_diario_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
        importe_sdp = saldo_diario_posterior.importe

        mov.importe += 20
        mov.dia = dia_tardio
        mov.clean_save()

        saldo_diario_posterior.refresh_from_db()
        assert saldo_diario_posterior.importe == importe_sdp - importe_mov

    def test_si_cambia_importe_y_fecha_por_fecha_posterior_con_movimientos_de_la_cuenta_resta_importe_viejo_y_suma_importe_nuevo_a_saldo_diario_de_dia_nuevo(
            self, sentido, salida_posterior, entrada_tardia, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        importe_mov = mov.importe_cta(sentido)
        saldo_diario_tardio = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_tardia.dia)
        importe_sdt = saldo_diario_tardio.importe

        mov.importe += 20
        mov.dia = entrada_tardia.dia
        mov.clean_save()

        saldo_diario_tardio.refresh_from_db()
        assert saldo_diario_tardio.importe == importe_sdt - importe_mov + mov.importe_cta(sentido)

    def test_si_cambia_importe_y_fecha_por_fecha_posterior_sin_movimientos_de_la_cuenta_crea_saldo_diario_calculando_importe_nuevo(
            self, sentido, salida_posterior, dia_tardio, request, mocker):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")

        mov.importe += 20
        mov.dia = dia_tardio
        mov.clean_save()
        importe_sp = saldo_posterior.tomar_de_bd().importe

        mock_crear.assert_called_once_with(
            cuenta=cuenta,
            dia=dia_tardio,
            importe=importe_sp + mov.importe_cta(sentido)
        )

    def test_si_cambia_importe_y_fecha_por_fecha_anterior_suma_importe_nuevo_a_movimientos_intermedios(
            self, sentido, entrada_anterior, dia_temprano, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario_anterior = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_anterior.dia)
        importe_sda = saldo_diario_anterior.importe

        mov.importe += 20
        mov.dia = dia_temprano
        mov.clean_save()

        saldo_diario_anterior.refresh_from_db()
        assert saldo_diario_anterior.importe == importe_sda + mov.importe_cta(sentido)

    def test_si_cambia_importe_y_fecha_por_fecha_anterior_con_movimientos_de_la_cuenta_suma_importe_nuevo_a_saldo_diario_de_la_nueva_fecha(
            self, sentido, entrada_anterior, entrada_temprana, request):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        saldo_diario_temprano = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_temprana.dia)
        importe_sdt = saldo_diario_temprano.importe

        mov.importe += 20
        mov.dia = entrada_temprana.dia
        mov.clean_save()

        saldo_diario_temprano.refresh_from_db()
        assert saldo_diario_temprano.importe == importe_sdt + mov.importe_cta(sentido)

    def test_si_cambia_importe_y_fecha_por_fecha_anterior_sin_movimientos_de_la_cuenta_crea_saldo_diario_con_importe_nuevo(
            self, sentido, salida_posterior, dia_temprano, request, mocker):
        mov = request.getfixturevalue(sentido)
        cuenta = getattr(mov, f"cta_{sentido}")
        mock_crear = mocker.patch("diario.models.movimiento.SaldoDiario.crear")

        mov.importe += 20
        mov.dia = dia_temprano
        mov.clean_save()

        mock_crear.assert_called_once_with(
            cuenta=cuenta,
            dia=dia_temprano,
            importe=mov.importe_cta(sentido)
        )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaCuentasYFecha:

    @pytest.mark.parametrize("fixt_dia", ["dia_temprano", "dia_tardio"])
    def test_en_movimiento_unico_de_la_cuenta_reemplazada_en_el_dia_reemplazado_elimina_saldo_del_dia_reemplazado(
            self, cuenta, cuenta_2, sentido, fixt_dia, entrada_anterior, dia_posterior, request, mocker):
        mov = request.getfixturevalue(sentido)
        dia = request.getfixturevalue(fixt_dia)
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        mock_delete = mocker.patch("diario.models.SaldoDiario.delete", autospec=True)

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.dia = dia
        mov.clean_save()

        mock_delete.assert_called_once_with(saldo_diario)

    def test_a_dia_posterior_en_movimiento_no_unico_de_la_cuenta_reemplazada_en_el_dia_reemplazado_resta_importe_de_saldo_de_cuenta_en_dia_reemplazado(
            self, cuenta, cuenta_2, sentido, traspaso, entrada_anterior, dia_posterior, request):
        mov = request.getfixturevalue(sentido)
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        importe_sd = saldo_diario.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.dia = dia_posterior
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd - mov.importe_cta(sentido)

    @pytest.mark.parametrize("otros_movs", [[], ["traspaso"]])
    def test_a_dia_posterior_resta_importe_de_saldos_intermedios_de_cuenta_reemplazada(
            self, cuenta, cuenta_2, sentido, otros_movs, entrada_anterior, salida_posterior, dia_tardio, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        saldo_diario_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
        importe_sdp = saldo_diario_posterior.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.dia = dia_tardio
        mov.clean_save()

        saldo_diario_posterior.refresh_from_db()
        assert saldo_diario_posterior.importe == importe_sdp - mov.importe_cta(sentido)

    @pytest.mark.parametrize("otros_movs", [[], ["traspaso"]])
    def test_a_dia_posterior_no_modifica_saldos_intermedios_de_cuenta_nueva(
            self, sentido, otros_movs, entrada_anterior_otra_cuenta, entrada_posterior_otra_cuenta, dia_tardio, cuenta_2, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        saldo_diario_posterior = SaldoDiario.tomar(cuenta=cuenta_2, dia=entrada_posterior_otra_cuenta.dia)
        importe_sdp = saldo_diario_posterior.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.dia = dia_tardio
        mov.clean_save()

        saldo_diario_posterior.refresh_from_db()
        assert saldo_diario_posterior.importe == importe_sdp

    @pytest.mark.parametrize("otros_movs", [[], ["traspaso"]])
    def test_a_dia_anterior_no_modifica_saldos_intermedios_de_cuenta_reemplazada(
            self, sentido, otros_movs, dia_temprano, entrada_anterior, cuenta, cuenta_2, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        saldo_diario_anterior = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_anterior.dia)
        importe_sda = saldo_diario_anterior.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.dia = dia_temprano
        mov.clean_save()

        saldo_diario_anterior.refresh_from_db()
        assert saldo_diario_anterior.importe == importe_sda

    @pytest.mark.parametrize("fixt_dia", ["dia_temprano", "dia_tardio"])
    def test_a_dia_sin_movimientos_de_la_cuenta_nueva_crea_saldo_de_cuenta_nueva_en_nuevo_dia(
            self, sentido, cuenta_2, fixt_dia, request, mocker):
        mov = request.getfixturevalue(sentido)
        dia = request.getfixturevalue(fixt_dia)
        mock_crear = mocker.patch("diario.models.SaldoDiario.crear")

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.dia = dia
        mov.clean_save()

        mock_crear.assert_called_once_with(
            cuenta=cuenta_2,
            dia=dia,
            importe=mov.importe_cta(sentido)
        )

    @pytest.mark.parametrize("otro_mov", ["entrada_anterior_otra_cuenta", "entrada_posterior_otra_cuenta"])
    def test_a_dia_con_movimientos_de_la_cuenta_nueva_suma_importe_a_saldo_de_cuenta_nueva_en_nuevo_dia(
            self, sentido, otro_mov, cuenta_2, entrada_posterior_otra_cuenta, request):
        mov = request.getfixturevalue(sentido)
        otro_mov = request.getfixturevalue(otro_mov)
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta_2, dia=otro_mov.dia)
        importe_sd = saldo_diario.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.dia = otro_mov.dia
        mov.clean_save()

        saldo_diario.refresh_from_db()
        assert saldo_diario.importe == importe_sd + mov.importe_cta(sentido)

    @pytest.mark.parametrize("otros_movs", [[], ["salida_tardia_otra_cuenta"]])
    def test_a_dia_posterior_no_modifica_saldos_diarios_intermedios_de_cuenta_nueva(
            self, sentido, cuenta_2, otros_movs, entrada_posterior_otra_cuenta, dia_tardio, request):
        mov = request.getfixturevalue(sentido)
        for otro_mov in otros_movs:
            request.getfixturevalue(otro_mov)
        saldo_diario_posterior = SaldoDiario.tomar(cuenta=cuenta_2, dia=entrada_posterior_otra_cuenta.dia)
        importe_sdp = saldo_diario_posterior.importe

        setattr(mov, f"cta_{sentido}", cuenta_2)
        mov.dia = dia_tardio
        mov.clean_save()

        saldo_diario_posterior.refresh_from_db()
        assert saldo_diario_posterior.importe == importe_sdp


class TestSaveCambiaEsGratis:

    def test_mov_esgratis_true_elimina_contramovimiento(self, credito):
        id_contramov = credito.id_contramov
        credito.esgratis = True
        credito.clean_save()

        with pytest.raises(Movimiento.DoesNotExist):
            Movimiento.tomar(id=id_contramov)

    def test_mov_esgratis_false_genera_contramovimiento(self, donacion):
        donacion.esgratis = False
        donacion.clean_save()

        assert donacion.id_contramov is not None
        assert Movimiento.tomar(id=donacion.id_contramov).concepto == donacion.concepto
        assert Movimiento.tomar(id=donacion.id_contramov).detalle == "Constitución de crédito"


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
class TestSaveCambiaMoneda:
    def test_si_cambia_moneda_en_traspaso_entre_cuentas_en_distinta_moneda_no_modifica_saldos_diarios_de_cuentas_o_casi(
            self, sentido, euro, request):
        mov = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        cuenta = getattr(mov, f"cta_{sentido}")
        contracuenta = getattr(mov, f"cta_{el_que_no_es(sentido, 'entrada', 'salida')}")
        saldo_diario_cuenta = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        saldo_diario_contracuenta = SaldoDiario.tomar(cuenta=contracuenta, dia=mov.dia)
        importe_sdc = saldo_diario_cuenta.importe
        importe_sdcc = saldo_diario_contracuenta.importe
        mov.moneda = euro
        mov.clean_save()

        assert saldo_diario_cuenta.tomar_de_bd().importe == pytest.approx(importe_sdc, abs=0.0101)
        assert saldo_diario_contracuenta.tomar_de_bd().importe == importe_sdcc

    def test_si_cambia_cotizacion_en_traspaso_entre_cuentas_en_distinta_moneda_cambia_importe_de_saldo_diario_de_cuenta_en_moneda_distinta_de_la_del_movimiento(
            self, sentido, request):
        mov = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        opuesto = el_que_no_es(sentido, 'entrada', 'salida')
        cuenta = getattr(mov, f"cta_{sentido}")
        contracuenta = getattr(mov, f"cta_{opuesto}")
        importe_cc =mov.importe_cta(opuesto)
        saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
        importe_sd = saldo_diario.importe
        saldo_diario_cc = SaldoDiario.tomar(cuenta=contracuenta, dia=mov.dia)
        importe_sdcc = saldo_diario_cc.importe

        mov.cotizacion = 4
        mov.clean_save()

        assert saldo_diario.tomar_de_bd().importe == importe_sd
        assert saldo_diario_cc.tomar_de_bd().importe == importe_sdcc - importe_cc +mov.importe_cta(opuesto)

    def test_si_cambia_cotizacion_en_traspaso_entre_cuentas_en_distinta_moneda_cambia_importe_de_cuenta_en_otra_moneda(
            self, sentido, request):
        movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
        importe = abs(movimiento.importe_cta(sentido))

        movimiento.cotizacion = 4
        movimiento.clean_save()

        assert abs(movimiento.importe_cta(sentido)) == importe
        assert abs(movimiento.importe_cta(sentido_otra_cuenta)) == importe * 4

    # Cambia moneda no cambia cotización no cambia importe
    def test_si_cambia_moneda_en_traspaso_entre_cuentas_en_distinta_moneda_se_recalcula_cotizacion_e_importe(
            self, sentido, euro, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        cotizacion = mov_distintas_monedas.cotizacion
        importe = mov_distintas_monedas.importe
        importe_ce = mov_distintas_monedas.importe_cta_entrada
        importe_cs = mov_distintas_monedas.importe_cta_salida

        mov_distintas_monedas.moneda = euro
        mov_distintas_monedas.clean_save()

        assert round(mov_distintas_monedas.cotizacion, 2) == round(1 / cotizacion, 2)
        assert mov_distintas_monedas.importe == round(importe / mov_distintas_monedas.cotizacion, 2)
        assert mov_distintas_monedas.importe_cta_entrada == pytest.approx(importe_ce, abs=0.01)
        assert mov_distintas_monedas.importe_cta_salida == importe_cs

    # Cambia moneda cambia cotización no cambia importe
    def test_si_cambia_moneda_y_cotizacion_en_traspaso_entre_cuentas_en_distinta_moneda_toma_cotizacion_pasada_manualmente(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
        otra_cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}")
        importe = mov_distintas_monedas.importe

        mov_distintas_monedas.moneda = otra_cuenta.moneda
        mov_distintas_monedas.cotizacion = 4
        mov_distintas_monedas.clean_save()

        assert mov_distintas_monedas.cotizacion == 4
        assert mov_distintas_monedas.importe == importe / mov_distintas_monedas.cotizacion
        assert abs(mov_distintas_monedas.importe_cta(sentido)) == importe
        assert abs(mov_distintas_monedas.importe_cta(sentido_otra_cuenta)) == importe / 4

    # Cambia moneda cambia cotización cambia importe
    def test_si_cambia_moneda_cotizacion_e_importe_cambian_importes_cta_entrada_y_cta_salida(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')
        otra_cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}")

        mov_distintas_monedas.moneda = otra_cuenta.moneda
        mov_distintas_monedas.cotizacion = 4
        mov_distintas_monedas.importe = 5
        mov_distintas_monedas.clean_save()

        assert mov_distintas_monedas.cotizacion == 4
        assert mov_distintas_monedas.importe == 5
        assert abs(mov_distintas_monedas.importe_cta(sentido_otra_cuenta)) == mov_distintas_monedas.importe
        assert abs(mov_distintas_monedas.importe_cta(sentido)) == (5 * 4)

    # Cambia moneda no cambia cotización cambia importe
    def test_si_cambia_moneda_e_importe_se_recalcula_cotizacion(self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')
        otra_cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}")
        cotizacion = mov_distintas_monedas.cotizacion

        mov_distintas_monedas.moneda = otra_cuenta.moneda
        mov_distintas_monedas.importe = 5
        mov_distintas_monedas.clean_save()

        assert round(mov_distintas_monedas.cotizacion, 2) == round(1 / cotizacion, 2)
        assert mov_distintas_monedas.importe == 5
        assert \
            abs(mov_distintas_monedas.importe_cta(sentido_otra_cuenta)) == \
            mov_distintas_monedas.importe
        assert \
            abs(mov_distintas_monedas.importe_cta(sentido)) == \
            round(5* mov_distintas_monedas.cotizacion, 2)

    # No cambia moneda cambia cotización no cambia importe
    def test_si_cambia_cotizacion_en_traspaso_entre_cuentas_en_distinta_moneda_no_cambia_importe_del_movimiento(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')

        # importe_cta_salida = mov_distintas_monedas.importe_cta_salida
        importe = mov_distintas_monedas.importe

        mov_distintas_monedas.cotizacion = 2
        mov_distintas_monedas.clean_save()

        assert mov_distintas_monedas.cotizacion == 2
        assert mov_distintas_monedas.importe == importe
        assert \
            abs(mov_distintas_monedas.importe_cta(sentido_otra_cuenta)) == \
            mov_distintas_monedas.importe * 2
        assert abs(mov_distintas_monedas.importe_cta(sentido)) == importe

    # No cambia moneda cambia cotización cambia importe
    def test_si_cambia_cotizacion_e_importe_en_traspaso_entre_cuentas_en_distinta_moneda_se_guardan_valores_ingresados(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')

        mov_distintas_monedas.cotizacion = 2
        mov_distintas_monedas.importe = 25
        mov_distintas_monedas.clean_save()

        assert mov_distintas_monedas.cotizacion == 2
        assert mov_distintas_monedas.importe == 25
        assert abs(mov_distintas_monedas.importe_cta(sentido)) == 25
        assert abs(mov_distintas_monedas.importe_cta(sentido_otra_cuenta)) == 25 * 2

    # No cambia moneda no cambia cotización cambia importe
    def test_si_cambia_importe_en_traspaso_entre_cuentas_en_distinta_moneda_se_guarda_importe_y_no_cambia_cotizacion(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')
        cotizacion = mov_distintas_monedas.cotizacion

        mov_distintas_monedas.importe = 25
        mov_distintas_monedas.clean_save()

        assert mov_distintas_monedas.cotizacion == cotizacion
        assert mov_distintas_monedas.importe == 25
        assert abs(mov_distintas_monedas.importe_cta(sentido)) == 25
        assert \
            abs(mov_distintas_monedas.importe_cta(sentido_otra_cuenta)) == \
            round(25 * mov_distintas_monedas.cotizacion, 2)
