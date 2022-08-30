from datetime import timedelta, date
from typing import Tuple

import pytest
from django.core.exceptions import ValidationError

from diario.models import Movimiento, Cuenta, CuentaInteractiva, Saldo
from utils.helpers_tests import dividir_en_dos_subcuentas


def signo(condicion: bool) -> int:
    return 1 if condicion else -1


def inferir_fixtures(sentido: str, request) -> Tuple[Movimiento, int, CuentaInteractiva]:
    mov = request.getfixturevalue(sentido)
    return mov, signo(sentido == 'entrada'), getattr(mov, f'cta_{sentido}')


@pytest.fixture
def credito_no_guardado(cuenta: CuentaInteractiva, cuenta_ajena: CuentaInteractiva) -> Movimiento:
    return Movimiento(
        concepto='Crédito',
        importe=30,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena
    )


class TestSaveGeneral:
    def test_no_modifica_saldo_en_mov_si_no_se_modifica_importe_ni_cuentas_ni_fecha(
            self, traspaso, mocker):
        mock_saldo_save = mocker.patch('diario.models.movimiento.Saldo.save')
        traspaso.concepto = 'Otro concepto'
        traspaso.save()
        mock_saldo_save.assert_not_called()

    def test_integrativo_no_modifica_saldo_en_mov_si_no_se_modifica_importe_ni_cuentas_ni_fecha(
            self, traspaso):
        saldo_ce = traspaso.cta_entrada.saldo_en_mov(traspaso)
        saldo_cs = traspaso.cta_salida.saldo_en_mov(traspaso)

        traspaso.concepto = 'Depósito en efectivo'
        traspaso.save()

        assert traspaso.cta_entrada.saldo_en_mov(traspaso) == saldo_ce
        assert traspaso.cta_salida.saldo_en_mov(traspaso) == saldo_cs


class TestSaveMovimientoEntreCuentasDeDistintosTitulares:
    def test_con_dos_cuentas_de_titulares_distintos_crea_dos_cuentas_credito(self, credito_no_guardado):
        credito_no_guardado.save()
        assert Cuenta.cantidad() == 4

        cc1 = list(Cuenta.todes())[-2]
        cc2 = list(Cuenta.todes())[-1]
        assert cc1.slug == '_otro-titular'
        assert cc2.slug == '_titular-otro'

    def test_con_dos_cuentas_de_titulares_distintos_guarda_cuentas_credito_como_contracuentas(
            self, credito_no_guardado):
        credito_no_guardado.save()
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
        credito.save()

        with pytest.raises(Movimiento.DoesNotExist):
            Movimiento.tomar(id=id_contramovimiento)

        assert credito.id_contramov is None

    @pytest.mark.parametrize('campo_cuenta, slug_ce, slug_cs', [
        ('cta_entrada', '_otro-gordo', '_gordo-otro'),
        ('cta_salida', '_gordo-titular', '_titular-gordo'),
    ])
    def test_cambiar_cuenta_de_movimiento_entre_titulares_por_cuenta_de_otro_titular_cambia_cuentas_en_contramovimiento(
            self, credito, campo_cuenta, slug_ce, slug_cs, titular_gordo):
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
            self, credito, campo_cuenta, fixt_cuenta, request):
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
    def test_cambiar_campo_sensible_de_movimiento_entre_titulares_regenera_contramovimiento(
            self, credito, campo, fixt, request):
        valor = request.getfixturevalue(fixt)
        id_contramov = credito.id_contramov
        setattr(credito, campo, valor)
        credito.save()
        assert credito.id_contramov != id_contramov

    @pytest.mark.parametrize('campo, valor', [
        ('concepto', 'otro concepto'),
        ('detalle', 'otro detalle'),
        ('orden_dia', 0)
    ])
    def test_cambiar_campo_no_sensible_de_movimiento_entre_titulares_no_regenera_contramovimiento(
            self, credito, campo, valor, request):
        id_contramov = credito.id_contramov
        setattr(credito, campo, valor)
        credito.save()
        assert credito.id_contramov == id_contramov

    @pytest.mark.parametrize('campo,fixt', [
        ('importe', 'importe_alto'),
        ('fecha', 'fecha_tardia'),
    ])
    def test_cambiar_campo_sensible_de_movimiento_entre_titulares_cambia_el_mismo_campo_en_contramovimiento(
            self, credito, campo, fixt, request):
        valor = request.getfixturevalue(fixt)
        setattr(credito, campo, valor)
        credito.save()
        contramov = Movimiento.tomar(id=credito.id_contramov)
        assert getattr(contramov, campo) == valor


class TestSaveModificaImporte:

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_resta_importe_antiguo_y_suma_el_nuevo_a_saldo_de_cuenta_en_movimiento(
            self, sentido, importe_alto, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        importe_mov = mov.importe
        saldo_cuenta = cuenta.saldo_en_mov(mov)

        mov.importe = importe_alto
        mov.save()

        assert \
            cuenta.saldo_en_mov(mov) == \
            saldo_cuenta - importe_mov*s + importe_alto*s

    def test_en_mov_de_traspaso_modifica_saldo_de_ambas_cuentas(
            self, traspaso, importe_alto):
        saldo_ce = traspaso.saldo_ce()
        saldo_cs = traspaso.saldo_cs()
        importe_saldo_ce = saldo_ce.importe
        importe_saldo_cs = saldo_cs.importe
        importe_mov = traspaso.importe

        traspaso.importe = importe_alto
        traspaso.save()
        saldo_ce.refresh_from_db(fields=['_importe'])
        saldo_cs.refresh_from_db(fields=['_importe'])

        assert saldo_ce.importe == importe_saldo_ce - importe_mov + importe_alto
        assert saldo_cs.importe == importe_saldo_cs + importe_mov - importe_alto

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_actualiza_saldos_posteriores_de_cta_entrada(
            self, sentido, salida_posterior, importe_alto, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        importe_mov = mov.importe
        saldo_posterior_cuenta = cuenta.saldo_en_mov(salida_posterior)

        mov.importe = importe_alto
        mov.save()

        assert \
            cuenta.saldo_en_mov(salida_posterior) == \
            saldo_posterior_cuenta - importe_mov*s + importe_alto*s

    def test_en_mov_traspaso_con_contramov_cambia_saldo_en_las_cuentas_del_contramov(
            self, credito, importe_alto):
        importe_mov = credito.importe
        contramov = Movimiento.tomar(id=credito.id_contramov)
        cta_deudora = contramov.cta_salida
        cta_acreedora = contramov.cta_entrada
        saldo_cd = cta_deudora.saldo
        saldo_ca = cta_acreedora.saldo

        credito.importe = importe_alto
        credito.save()

        assert cta_deudora.saldo == saldo_cd + importe_mov - importe_alto
        assert cta_acreedora.saldo == saldo_ca - importe_mov + importe_alto


class TestSaveCambiaCuentas:

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_genera_saldo_de_cuenta_nueva_y_elimina_el_de_cuenta_vieja_en_movimiento(
            self, mocker, sentido, cuenta_2, request):
        campo_cuenta = f'cta_{sentido}'
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo_en_mov_viejo = Saldo.tomar(cuenta=cuenta, movimiento=mov)
        mock_generar = mocker.patch('diario.models.movimiento.Saldo.generar')
        mock_eliminar = mocker.patch('diario.models.movimiento.Saldo.eliminar', autospec=True)

        setattr(mov, campo_cuenta, cuenta_2)
        mov.save()

        mock_generar.assert_called_once_with(mov, salida=sentido == 'salida')
        mock_eliminar.assert_called_once_with(saldo_en_mov_viejo)

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_actualiza_importe_de_saldos_posteriores_de_cuenta_original_y_nueva(
            self, sentido, entrada_otra_cuenta, salida_posterior, request):
        campo_cuenta = f'cta_{sentido}'
        mov, s, cuenta = inferir_fixtures(sentido, request)
        cuenta_2 = entrada_otra_cuenta.cta_entrada
        saldo_posterior_cuenta = cuenta.saldo_en_mov(salida_posterior)
        saldo_posterior_cuenta_2 = cuenta_2.saldo_en_mov(salida_posterior)

        setattr(mov, campo_cuenta, cuenta_2)
        mov.save()

        assert \
            cuenta.saldo_en_mov(salida_posterior) == \
            saldo_posterior_cuenta - mov.importe*s
        assert \
            cuenta_2.saldo_en_mov(salida_posterior) == \
            saldo_posterior_cuenta_2 + mov.importe*s

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_funciona_en_movimientos_de_traspaso(self, sentido, traspaso, cuenta_3):
        campo_cuenta = f'cta_{sentido}'
        cuenta = getattr(traspaso, campo_cuenta)

        setattr(traspaso, campo_cuenta, cuenta_3)
        traspaso.save()

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta, movimiento=traspaso)

        assert cuenta_3.saldo_set.count() == 1
        assert \
            cuenta_3.saldo_en_mov(traspaso) == \
            traspaso.importe * signo(sentido == 'entrada')

    def test_modificar_ambas_cuentas_funciona_en_movimientos_de_traspaso(
            self, traspaso, cuenta_3, cuenta_4):

        cuenta_1 = traspaso.cta_entrada
        cuenta_2 = traspaso.cta_salida

        traspaso.cta_entrada = cuenta_3
        traspaso.cta_salida = cuenta_4
        traspaso.save()

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta_1, movimiento=traspaso)
        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta_2, movimiento=traspaso)

        assert cuenta_3.saldo_set.count() == 1
        assert cuenta_3.saldo_en_mov(traspaso) == traspaso.importe
        assert cuenta_4.saldo_set.count() == 1
        assert cuenta_4.saldo_en_mov(traspaso) == -traspaso.importe

    def test_modificar_ambas_cuentas_en_movimientos_de_traspaso_actualiza_importes_de_saldos_posteriores_de_las_cuatro_cuentas(
            self, traspaso, salida_posterior, cuenta_3, cuenta_4):
        cuenta_1 = traspaso.cta_entrada
        cuenta_2 = traspaso.cta_salida

        # Generar saldos para cuentas que aún no lo tienen o van a perderlo
        Movimiento.crear('mov cta2', 15, cuenta_2, fecha=traspaso.fecha)
        Movimiento.crear('mov cta3', 15, cuenta_3, fecha=traspaso.fecha)
        Movimiento.crear('mov cta4', 18, cuenta_4, fecha=traspaso.fecha)

        saldo_posterior_cuenta_2 = cuenta_2.saldo_en_mov(salida_posterior)
        saldo_posterior_cuenta_1 = cuenta_1.saldo_en_mov(salida_posterior)
        saldo_posterior_cuenta_3 = cuenta_3.saldo_en_mov(salida_posterior)
        saldo_posterior_cuenta_4 = cuenta_4.saldo_en_mov(salida_posterior)

        traspaso.cta_entrada = cuenta_3
        traspaso.cta_salida = cuenta_4
        traspaso.save()

        assert \
            cuenta_1.saldo_en_mov(salida_posterior) == \
            saldo_posterior_cuenta_1 - traspaso.importe
        assert \
            cuenta_2.saldo_en_mov(salida_posterior) == \
            saldo_posterior_cuenta_2 + traspaso.importe
        assert \
            cuenta_3.saldo_en_mov(salida_posterior) == \
            saldo_posterior_cuenta_3 + traspaso.importe
        assert \
            cuenta_4.saldo_en_mov(salida_posterior) == \
            saldo_posterior_cuenta_4 - traspaso.importe

    def test_intercambiar_cuentas_resta_importe_x2_de_saldo_en_movimiento_de_cta_entrada_y_lo_suma_a_saldo_en_movimiento_de_cta_salida(
            self, traspaso):
        c1 = traspaso.cta_entrada
        c2 = traspaso.cta_salida
        saldo_c1 = c1.saldo_en_mov(traspaso)
        saldo_c2 = c2.saldo_en_mov(traspaso)
        traspaso.cta_salida = c1
        traspaso.cta_entrada = c2
        traspaso.save()

        assert c1.saldo_en_mov(traspaso) == saldo_c1 - traspaso.importe * 2
        assert c2.saldo_en_mov(traspaso) == saldo_c2 + traspaso.importe * 2

    def test_intercambiar_cuentas_actualiza_importes_de_saldos_posteriores_de_cuentas_intercambiadas(
            self, traspaso, salida_posterior):
        c1 = traspaso.cta_entrada
        c2 = traspaso.cta_salida
        saldo_posterior_c1 = c1.saldo_en_mov(salida_posterior)
        saldo_posterior_c2 = c2.saldo_en_mov(salida_posterior)
        traspaso.cta_salida = c1
        traspaso.cta_entrada = c2
        traspaso.save()

        assert c1.saldo_en_mov(salida_posterior) == saldo_posterior_c1 - traspaso.importe * 2
        assert c2.saldo_en_mov(salida_posterior) == saldo_posterior_c2 + traspaso.importe * 2

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_si_cuenta_pasa_al_lugar_opuesto_suma_o_resta_dos_veces_el_importe_al_saldo_de_la_cuenta_y_posteriores(
            self, sentido, salida_posterior, request):
        campo_cuenta = f'cta_{sentido}'
        mov, s, cuenta = inferir_fixtures(sentido, request)
        contracampo = 'cta_salida' if campo_cuenta == 'cta_entrada' else 'cta_entrada'
        saldo_cuenta = cuenta.saldo_en_mov(mov)
        saldo_posterior_cuenta = cuenta.saldo_en_mov(salida_posterior)
        diferencia = -s * mov.importe * 2

        setattr(mov, contracampo, cuenta)
        setattr(mov, campo_cuenta, None)
        mov.save()

        assert cuenta.saldo_en_mov(mov) == saldo_cuenta + diferencia
        assert cuenta.saldo_en_mov(salida_posterior) == saldo_posterior_cuenta + diferencia

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_si_cuenta_pasa_al_lugar_opuesto_y_se_cambia_por_cuenta_nueva_en_traspaso_se_suma_importe_duplicado_a_saldo_en_mov_y_posteriores_y_desaparece_saldo_de_cuenta_reemplazada(
            self, traspaso, salida_posterior, sentido, cuenta_3):
        campo_cuenta = f'cta_{sentido}'
        s = signo(sentido == 'entrada')
        contracampo = 'cta_salida' if campo_cuenta == 'cta_entrada' else 'cta_entrada'
        cuenta = getattr(traspaso, campo_cuenta)
        contracuenta = getattr(traspaso, contracampo)
        saldo_contracuenta = contracuenta.saldo_en_mov(traspaso)
        saldo_posterior_contracuenta = contracuenta.saldo_en_mov(salida_posterior)

        setattr(traspaso, campo_cuenta, contracuenta)
        setattr(traspaso, contracampo, cuenta_3)
        traspaso.save()

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta, movimiento=traspaso)

        assert contracuenta.saldo_en_mov(traspaso) == saldo_contracuenta + traspaso.importe * s * 2
        assert contracuenta.saldo_en_mov(salida_posterior) == saldo_posterior_contracuenta + traspaso.importe * s * 2
        assert cuenta_3.saldo_set.count() == 1
        assert cuenta_3.saldo_en_mov(traspaso) == -traspaso.importe * s
        assert cuenta_3.saldo_en_mov(salida_posterior) == -traspaso.importe * s

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_si_desaparece_cuenta_en_mov_traspaso_se_elimina_saldo_de_cuenta_en_movimiento_y_se_actualizan_saldos_posteriores(
            self, traspaso, salida_posterior, sentido):
        campo_cuenta = f'cta_{sentido}'
        cuenta = getattr(traspaso, campo_cuenta)
        saldo_posterior = cuenta.saldo_en_mov(salida_posterior)

        setattr(traspaso, campo_cuenta, None)
        traspaso.save()

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta, movimiento=traspaso)

        assert cuenta.saldo_en_mov(salida_posterior) == saldo_posterior - traspaso.importe * signo(sentido == 'entrada')

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_si_aparece_cuenta_donde_no_la_habia_en_movimiento_aparece_saldo_en_movimiento_en_cuenta_nueva(
            self, sentido, cuenta_2, request):
        mov, s, _ = inferir_fixtures(sentido, request)
        campo_cuenta_vacio = 'cta_salida' if sentido == 'entrada' else 'cta_entrada'

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta_2, movimiento=mov)

        setattr(mov, campo_cuenta_vacio, cuenta_2)
        mov.save()

        assert cuenta_2.saldo_en_mov(mov) == -s * mov.importe

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_cambiar_cuenta_por_cuentata_de_otro_titular_en_movimientos_con_contramovimiento_regenera_contramovimiento(
            self, sentido, credito, cuenta_gorda, mocker):
        mock_regenerar_contramovimiento = mocker.patch(
            'diario.models.Movimiento._regenerar_contramovimiento',
            autospec=True
        )
        setattr(credito, f'cta_{sentido}', cuenta_gorda)
        credito.save()

        mock_regenerar_contramovimiento.assert_called_once_with(credito)

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_cambiar_cuenta_por_cuenta_de_otro_titular_en_movimiento_de_traspaso_con_contramovimiento_modifica_contramovimiento(
            self, sentido, credito, cuenta_gorda):
        contramov = Movimiento.tomar(id=credito.id_contramov)
        contrasentido = 'entrada' if sentido == 'salida' else 'salida'
        cuenta_contramov = getattr(contramov, f'cta_{contrasentido}')

        setattr(credito, f'cta_{sentido}', cuenta_gorda)
        credito.save()

        contramov = Movimiento.tomar(id=credito.id_contramov)
        assert getattr(contramov, f'cta_{contrasentido}').id != cuenta_contramov
        assert cuenta_gorda.titular.titname in getattr(contramov, f'cta_{contrasentido}').slug

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_cambiar_cuentaa_por_cuenta_de_otro_titular_en_movimiento_de_traspaso_sin_contramovimiento_genera_contramovimiento(
            self, sentido, traspaso, cuenta_ajena, mocker):
        mock_crear_movimiento_credito = mocker.patch(
            'diario.models.Movimiento._crear_movimiento_credito',
            autospec=True
        )
        setattr(traspaso, f'cta_{sentido}', cuenta_ajena)
        traspaso.save()

        mock_crear_movimiento_credito.assert_called_once_with(traspaso)

    @pytest.mark.parametrize('sentido, fixt_cuenta', [
        ('entrada', 'cuenta_ajena_2'),
        ('salida', 'cuenta_2'),
    ])
    def test_cambiar_cuenta_de_otro_titular_por_cuenta_del_mismo_titular_en_movimiento_de_traspaso_con_contramovimiento_destruye_contramovimiento_y_no_lo_regenera(
            self, sentido, fixt_cuenta, credito, mocker, request):
        otra_cuenta = request.getfixturevalue(fixt_cuenta)
        mock_eliminar_contramovimiento = mocker.patch(
            'diario.models.Movimiento._eliminar_contramovimiento',
            autospec=True
        )
        mock_crear_movimiento_credito = mocker.patch(
            'diario.models.Movimiento._crear_movimiento_credito'
        )

        setattr(credito, f'cta_{sentido}', otra_cuenta)
        credito.save()

        mock_eliminar_contramovimiento.assert_called_once_with(credito)
        mock_crear_movimiento_credito.assert_not_called()


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaImporteYCuentas:
    def test_si_cambia_cuenta_e_importe_desaparece_saldo_en_movimiento_de_cuenta_anterior_y_aparece_el_de_la_nueva_con_el_nuevo_importe(
            self, sentido, cuenta_2, importe_alto, request):
        mov, s, cuenta_anterior = inferir_fixtures(sentido, request)
        cant_saldos = cuenta_2.saldo_set.count()

        setattr(mov, f'cta_{sentido}', cuenta_2)
        mov.importe = importe_alto
        mov.save()

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta_anterior, movimiento=mov)
        assert cuenta_2.saldo_set.count() == cant_saldos + 1
        assert cuenta_2.saldo_en_mov(mov) == s*importe_alto

    def test_si_cambia_cuenta_e_importe_en_mov_de_traspaso_desaparece_saldo_en_movimiento_de_cuenta_anterior_y_aparece_el_de_la_nueva_con_el_nuevo_importe_y_se_actualiza_importe_de_la_cuenta_no_cambiada(
            self, sentido, traspaso, cuenta_3, importe_alto):
        s = signo(sentido == 'entrada')
        contrasentido = 'salida' if sentido == 'entrada' else 'entrada'
        cuenta_anterior = getattr(traspaso, f'cta_{sentido}')
        cuenta_no_cambiada = getattr(traspaso, f'cta_{contrasentido}')
        importe_anterior = traspaso.importe
        saldo_anterior_cuenta_no_cambiada = cuenta_no_cambiada.saldo_en_mov(traspaso)
        cant_saldos = cuenta_3.saldo_set.count()

        setattr(traspaso, f'cta_{sentido}', cuenta_3)
        traspaso.importe = importe_alto
        traspaso.save()

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta_anterior, movimiento=traspaso)
        assert cuenta_3.saldo_set.count() == cant_saldos + 1
        assert cuenta_3.saldo_en_mov(traspaso) == s*importe_alto
        assert \
            cuenta_no_cambiada.saldo_en_mov(traspaso) == \
            saldo_anterior_cuenta_no_cambiada + s*importe_anterior - s*importe_alto


def cambiar_fecha(mov: Movimiento, fecha: date):
    mov.fecha = fecha
    mov.full_clean()
    mov.save()


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaFecha:

    def test_si_cambia_fecha_a_fecha_posterior_toma_primer_orden_dia_de_nueva_fecha(
            self, sentido, importe, salida_posterior, fecha_posterior, request):
        mov_ant, _, cuenta = inferir_fixtures(sentido, request)
        mov = Movimiento.crear('segundo del día', importe, cuenta, fecha=mov_ant.fecha)
        assert mov.orden_dia == 1

        cambiar_fecha(mov, fecha_posterior)

        assert mov.orden_dia == 0

    def test_si_cambia_fecha_a_fecha_anterior_toma_ultimo_orden_dia_de_nueva_fecha(
            self, sentido, entrada_anterior, fecha_anterior, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        cambiar_fecha(mov, fecha_anterior)

        assert mov.orden_dia > entrada_anterior.orden_dia

    def test_si_cambia_fecha_a_fecha_posterior_resta_importe_a_saldos_intermedios_de_cuenta_entre_antigua_y_nueva_posicion_de_movimiento(
            self, sentido, salida_posterior, entrada_tardia, fecha_tardia, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_intermedio = cuenta.saldo_en_mov(salida_posterior)

        cambiar_fecha(mov, fecha_tardia)

        assert cuenta.saldo_en_mov(salida_posterior) == saldo_intermedio - s*mov.importe

    def test_si_cambia_fecha_a_una_fecha_posterior_saldo_de_cuenta_en_mov_toma_importe_de_ultimo_saldo(
            self, sentido, salida_posterior, entrada_tardia, fecha_tardia_plus, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        ultimo_saldo = cuenta.saldo_en_mov(entrada_tardia)

        cambiar_fecha(mov, fecha_tardia_plus)

        assert cuenta.saldo_en_mov(mov) == ultimo_saldo

    def test_si_cambia_fecha_a_una_fecha_posterior_pero_anterior_a_todos_los_saldos_posteriores_de_cuenta_no_modifica_importe_de_ningun_saldo(
            self, sentido, entrada_tardia, fecha_posterior, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo = cuenta.saldo_en_mov(mov)
        saldo_tardio = cuenta.saldo_en_mov(entrada_tardia)

        cambiar_fecha(mov, fecha_posterior)

        assert cuenta.saldo_en_mov(mov) == saldo
        assert cuenta.saldo_en_mov(entrada_tardia) == saldo_tardio

    def test_si_cambia_fecha_a_una_fecha_posterior_no_modifica_importes_de_saldos_de_cuenta_posteriores_a_nueva_ubicacion_de_movimiento(
            self, sentido, salida_posterior, fecha_posterior, entrada_tardia, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo_tardio = cuenta.saldo_en_mov(entrada_tardia)

        cambiar_fecha(mov, fecha_posterior + timedelta(1))

        assert cuenta.saldo_en_mov(entrada_tardia) == saldo_tardio

    def test_si_cambia_fecha_a_una_fecha_posterior_no_modifica_importes_de_saldos_de_cuenta_anteriores_a_ubicacion_anterior_de_movimiento(
            self, sentido, fecha_posterior, entrada_anterior, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo_anterior = cuenta.saldo_en_mov(entrada_anterior)

        cambiar_fecha(mov, fecha_posterior)

        assert cuenta.saldo_en_mov(entrada_anterior) == saldo_anterior

    def test_si_cambia_fecha_a_fecha_anterior_suma_importe_a_saldos_intermedios_de_cuenta_entre_antigua_y_nueva_posicion_de_movimiento(
            self, sentido, fecha_temprana, entrada_temprana, entrada_anterior, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_anterior = cuenta.saldo_en_mov(entrada_anterior)

        cambiar_fecha(mov, fecha_temprana)

        assert cuenta.saldo_en_mov(entrada_anterior) == saldo_anterior + s*mov.importe

    def test_si_cambia_fecha_a_una_fecha_anterior_suma_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cuenta(
            self, sentido, entrada_temprana, entrada_anterior, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)

        cambiar_fecha(mov, entrada_temprana.fecha + timedelta(1))

        assert cuenta.saldo_en_mov(mov) == cuenta.saldo_en_mov(entrada_temprana) + s*mov.importe

    def test_si_cambia_fecha_a_una_fecha_anterior_y_no_hay_saldo_anterior_de_cuenta_asigna_importe_del_movimiento_a_saldo_de_cuenta_en_nueva_ubicacion_del_movimiento(
            self, sentido, fecha_temprana, entrada_anterior, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)

        cambiar_fecha(mov, fecha_temprana)

        assert cuenta.saldo_en_mov(mov) == s*mov.importe

    def test_si_cambia_fecha_a_una_fecha_anterior_no_modifica_importes_de_saldos_de_cuenta_anteriores_a_nueva_ubicacion_de_movimiento(
            self, sentido, entrada_temprana, entrada_anterior, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo_temprano = cuenta.saldo_en_mov(entrada_temprana)

        cambiar_fecha(mov, entrada_anterior.fecha)

        assert cuenta.saldo_en_mov(entrada_temprana) == saldo_temprano

    def test_si_cambia_fecha_a_una_fecha_anterior_no_modifica_importes_de_saldos_de_cta_entrada_posteriores_a_ubicacion_anterior_de_movimiento(
            self, sentido, entrada_anterior, salida_posterior, fecha_temprana, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo_posterior = cuenta.saldo_en_mov(salida_posterior)

        cambiar_fecha(mov, fecha_temprana)

        assert cuenta.saldo_en_mov(salida_posterior) == saldo_posterior


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

        cuenta = cuenta_con_saldo.tomar_del_slug()
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

        cuenta = cuenta.tomar_del_slug()
        mov1 = Movimiento.tomar(cta_entrada=subc1)

        assert cuenta.fecha_conversion == fecha_posterior
        assert mov1.fecha == fecha_posterior

    def test_no_permite_modificar_fecha_de_movimiento_de_traspaso_de_saldo_por_fecha_anterior_a_la_de_cualquier_otro_movimiento_de_la_cuenta_convertida(
            self, cuenta, entrada, fecha, fecha_anterior):
        subc1, subc2 = cuenta.dividir_entre(
            ['subc1', 'sc1', 10],
            ['subc2', 'sc2'],
            fecha=fecha,
        )
        mov1 = Movimiento.tomar(cta_entrada=subc1)
        mov1.fecha = fecha_anterior

        with pytest.raises(ValidationError):
            mov1.full_clean()
            mov1.save()


def cambiar_orden(mov: Movimiento, orden: int):
    mov.orden_dia = orden
    mov.full_clean()
    mov.save()


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaOrdenDia:
    def test_si_cambia_orden_dia_a_un_orden_posterior_resta_importe_de_saldos_intermedios_de_cuenta(
            self, sentido, entrada, salida, traspaso, entrada_otra_cuenta, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_traspaso = cuenta.saldo_en_mov(traspaso)

        cambiar_orden(mov, 3)

        assert cuenta.saldo_en_mov(traspaso) == saldo_traspaso - s*mov.importe

    def test_si_cambia_orden_dia_a_un_orden_posterior_saldo_de_cuenta_en_mov_cambiado_toma_valor_de_ultimo_saldo_anterior(
            self, sentido, entrada, salida, traspaso, entrada_otra_cuenta, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo_entrada_otra_cuenta = cuenta.saldo_en_mov(entrada_otra_cuenta)

        cambiar_orden(mov, 3)

        assert cuenta.saldo_en_mov(mov) == saldo_entrada_otra_cuenta

    def test_si_cambia_orden_dia_a_un_orden_posterior_no_modifica_importe_de_saldos_de_cuenta_posteriores_a_nueva_ubicacion_de_movimiento(
            self, sentido, entrada, salida, traspaso, entrada_otra_cuenta, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo_entrada_otra_cuenta = cuenta.saldo_en_mov(entrada_otra_cuenta)

        cambiar_orden(mov, 2)

        assert cuenta.saldo_en_mov(entrada_otra_cuenta) == saldo_entrada_otra_cuenta

    def test_si_cambia_orden_dia_a_un_orden_posterior_no_modifica_importes_de_saldos_de_cta_entrada_anteriores_a_ubicacion_anterior_de_movimiento(
            self, sentido, request):
        contrasentido = 'salida' if sentido == 'entrada' else 'entrada'
        mov_anterior = request.getfixturevalue(contrasentido)
        mov, _, cuenta = inferir_fixtures(sentido, request)
        request.getfixturevalue('traspaso')
        request.getfixturevalue('entrada_otra_cuenta')
        saldo_mov_anterior = cuenta.saldo_en_mov(mov_anterior)

        cambiar_orden(mov, 3)

        assert cuenta.saldo_en_mov(mov_anterior) == saldo_mov_anterior

    def test_si_cambia_orden_dia_a_un_orden_anterior_suma_importe_a_saldos_intermedios_de_cuenta(
            self, sentido, traspaso, entrada_otra_cuenta, entrada, salida, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_entrada_otra_cuenta = cuenta.saldo_en_mov(entrada_otra_cuenta)

        cambiar_orden(mov, 0)

        for m in (traspaso, entrada_otra_cuenta, entrada, salida):
            m.refresh_from_db(fields=['orden_dia'])

        assert cuenta.saldo_en_mov(entrada_otra_cuenta) == saldo_entrada_otra_cuenta + s*mov.importe

    def test_si_cambia_orden_dia_a_un_orden_anterior_suma_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cuenta(
            self, sentido, traspaso, entrada_otra_cuenta, entrada, salida, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)

        cambiar_orden(mov, 1)

        assert cuenta.saldo_en_mov(mov) == cuenta.saldo_en_mov(traspaso) + s*mov.importe

    def test_si_cambia_orden_dia_a_un_orden_anterior_y_no_hay_saldo_anterior_de_cta_entrada_asigna_importe_del_movimiento_a_saldo_de_cuenta_en_nueva_ubicacion_del_movimiento(
            self, sentido, traspaso, entrada_otra_cuenta, entrada, salida, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)

        cambiar_orden(mov, 0)

        assert cuenta.saldo_en_mov(mov) == s*mov.importe

    def test_si_cambia_orden_dia_a_un_orden_anterior_no_modifica_importes_de_saldos_de_cuenta_anteriores_a_nueva_ubicacion_de_movimiento(
            self, sentido, traspaso, entrada_otra_cuenta, entrada, salida, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo_traspaso = cuenta.saldo_en_mov(traspaso)

        cambiar_orden(mov, 1)

        assert cuenta.saldo_en_mov(traspaso) == saldo_traspaso

    def test_si_cambia_orden_dia_a_un_orden_anterior_no_modifica_importes_de_saldos_de_cuenta_posteriores_a_ubicacion_anterior_de_movimiento(
            self, sentido, traspaso, entrada_otra_cuenta, request):
        contrasentido = 'salida' if sentido == 'entrada' else 'entrada'
        mov, _, cuenta = inferir_fixtures(sentido, request)
        mov_posterior = request.getfixturevalue(contrasentido)
        saldo_mov_posterior = cuenta.saldo_en_mov(mov_posterior)

        cambiar_orden(mov, 0)
        assert cuenta.saldo_en_mov(mov_posterior) == saldo_mov_posterior
