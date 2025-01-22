from datetime import timedelta
from typing import Tuple

import pytest
from pytest import approx

from diario.models import Movimiento, Cuenta, CuentaInteractiva, Saldo, Dia
from utils.helpers_tests import \
    cambiar_fecha, cambiar_fecha_creacion, dividir_en_dos_subcuentas, signo
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
    def test_con_dos_cuentas_de_titulares_distintos_crea_dos_cuentas_credito(self, dia, credito_no_guardado):
        credito_no_guardado.full_clean()
        credito_no_guardado.save()
        assert Cuenta.cantidad() == 4

        cc1 = list(Cuenta.todes())[-1]
        cc2 = list(Cuenta.todes())[-2]
        assert cc1.slug == '_otro-titular'
        assert cc2.slug == '_titular-otro'

    def test_si_no_se_pasa_dia_ni_fecha_crea_cuentas_credito_con_fecha_ultimo_dia(self, dia, dia_posterior, credito_no_guardado):
        credito_no_guardado.dia = None
        credito_no_guardado.full_clean()
        credito_no_guardado.save()

        cc1 = list(Cuenta.todes())[-1]
        cc2 = list(Cuenta.todes())[-2]

        assert cc1.fecha_creacion == cc2.fecha_creacion == dia_posterior.fecha

    def test_con_dos_cuentas_de_titulares_distintos_guarda_cuentas_credito_como_contracuentas(
            self, dia, credito_no_guardado):
        credito_no_guardado.full_clean()
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
        ('importe', 'importe_aleatorio'),
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
        ('importe', 'importe_aleatorio'),
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
            self, sentido, importe_aleatorio, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        importe_mov = mov.importe
        saldo_cuenta = cuenta.saldo_en_mov(mov)

        mov.importe = importe_aleatorio
        mov.save()

        assert \
            cuenta.saldo_en_mov(mov) == \
            approx(saldo_cuenta - importe_mov * s + importe_aleatorio * s)

    def test_en_mov_de_traspaso_modifica_saldo_de_ambas_cuentas(
            self, traspaso, importe_aleatorio):
        saldo_ce = traspaso.saldo_ce()
        saldo_cs = traspaso.saldo_cs()
        importe_saldo_ce = saldo_ce.importe
        importe_saldo_cs = saldo_cs.importe
        importe_mov = traspaso.importe

        traspaso.importe = importe_aleatorio
        traspaso.save()
        saldo_ce.refresh_from_db(fields=['_importe'])
        saldo_cs.refresh_from_db(fields=['_importe'])

        assert saldo_ce.importe == approx(
            importe_saldo_ce - importe_mov + importe_aleatorio
        )
        assert saldo_cs.importe == approx(
            importe_saldo_cs + importe_mov - importe_aleatorio
        )

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_actualiza_saldos_posteriores_de_cta_entrada(
            self, sentido, salida_posterior, importe_aleatorio, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        importe_mov = mov.importe
        saldo_posterior_cuenta = cuenta.saldo_en_mov(salida_posterior)

        mov.importe = importe_aleatorio
        mov.save()

        assert \
            cuenta.saldo_en_mov(salida_posterior) == \
            approx(saldo_posterior_cuenta - importe_mov * s + importe_aleatorio * s)

    def test_en_mov_traspaso_con_contramov_cambia_saldo_en_las_cuentas_del_contramov(
            self, credito, importe_aleatorio):
        importe_mov = credito.importe
        contramov = Movimiento.tomar(id=credito.id_contramov)
        cta_deudora = contramov.cta_salida
        cta_acreedora = contramov.cta_entrada
        saldo_cd = cta_deudora.saldo
        saldo_ca = cta_acreedora.saldo

        credito.importe = importe_aleatorio
        credito.save()

        assert cta_deudora.saldo == approx(
            saldo_cd + importe_mov - importe_aleatorio
        )
        assert cta_acreedora.saldo == approx(
            saldo_ca - importe_mov + importe_aleatorio
        )


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
            saldo_posterior_cuenta - mov.importe * s
        assert \
            cuenta_2.saldo_en_mov(salida_posterior) == \
            saldo_posterior_cuenta_2 + mov.importe * s

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
    def test_si_aparece_cuenta_en_movimiento_donde_no_la_habia_aparece_saldo_en_movimiento_en_cuenta_nueva(
            self, sentido, cuenta_2, request):
        mov, s, _ = inferir_fixtures(sentido, request)
        campo_cuenta_vacio = 'cta_salida' if sentido == 'entrada' else 'cta_entrada'

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta_2, movimiento=mov)

        setattr(mov, campo_cuenta_vacio, cuenta_2)
        mov.save()

        assert cuenta_2.saldo_en_mov(mov) == -s * mov.importe

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_si_aparece_cuenta_de_otro_titular_en_movimiento_de_entrada_o_salida_se_genera_contramovimiento(
            self, sentido, cuenta_ajena, request):
        mov, s, _ = inferir_fixtures(sentido, request)
        campo_cuenta_vacio = 'cta_salida' if sentido == 'entrada' else 'cta_entrada'
        assert not mov.es_prestamo_o_devolucion()
        setattr(mov, campo_cuenta_vacio, cuenta_ajena)
        mov.save()
        assert mov.es_prestamo_o_devolucion()

    @pytest.mark.parametrize('sentido', ['entrada', 'salida'])
    def test_cambiar_cuenta_por_cuenta_de_otro_titular_en_movimientos_con_contramovimiento_regenera_contramovimiento(
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
    def test_cambiar_cuenta_por_cuenta_de_otro_titular_en_movimiento_de_traspaso_sin_contramovimiento_genera_contramovimiento(
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

    @pytest.mark.parametrize("sentido", ["salida", "entrada"])
    class TestSaveCambiaCuentasOtraMoneda:
        # Cambia cuenta en moneda del movimiento no cambia cotización no cambia importe
        # Venta de x reales en euros, a y reales el euro
        # - Es necesario cambiar la moneda del movimiento a reales
        # - Se calcula cotización y (euro.cotizacion_en(real))
        # - Se calcula importe x (imp_viejo / cot_vieja * cotización)
        # - No cambia importe_ce
        # - Cambia importe_cs (importe x)
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_una_tercera_moneda_se_recalculan_cotizacion_e_importe(
                self, sentido, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"
            moneda_otra_cuenta = getattr(movimiento, f"cta_{sentido_otra_cuenta}").moneda

            cotizacion = movimiento.cotizacion
            importe = movimiento.importe
            importes_ctas = {
                "importe_cta_entrada": movimiento.importe_cta_entrada,
                "importe_cta_salida": movimiento.importe_cta_salida,
            }

            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.full_clean()
            movimiento.save()
            print('cotización mov:', movimiento.cotizacion, movimiento.importe_cta_entrada, movimiento.importe_cta_salida)

            assert \
                movimiento.cotizacion == \
                moneda_otra_cuenta.cotizacion_en_al(real, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == round(importe / cotizacion * movimiento.cotizacion, 2)
            assert getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}") == pytest.approx(importes_ctas[f"importe_cta_{sentido_otra_cuenta}"], 0.001)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == abs(movimiento.importe)

        # Cambia cuenta en moneda del movimiento cambia cotización no cambia importe
        # Venta de x reales en euros, a 8 reales el euro
        # - Es necesario cambiar la moneda del movimiento a reales
        # - Se calcula importe x (imp_viejo / cot_vieja * 8)
        # - No cambia importe_ce
        # - Cambia importe_cs (importe x)
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_una_tercera_moneda_y_cotizacion_se_guarda_cotizacion_ingresada_y_se_recalcula_importe(
                self, sentido, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            cotizacion = movimiento.cotizacion
            importe = movimiento.importe
            importe_c = getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")

            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.cotizacion = 8
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 8
            assert movimiento.importe == round(importe / cotizacion * 8, 2)
            assert getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}") == importe_c
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == abs(movimiento.importe)

        # Cambia cuenta en moneda del movimiento cambia cotización cambia importe
        # Venta de 5 reales en euros, a 8 reales el euro
        # - Es necesario cambiar la moneda del movimiento a reales
        # - Cambia importe_ce (5 / 8)
        # - Cambia importe_cs (-5)
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_tercera_moneda_cotizacion_e_importe_se_guardan_valores_ingresados(
                self, sentido, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.cotizacion = 8
            movimiento.importe = 5
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 8
            assert movimiento.importe == 5
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == round(5/8, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == 5

        # Cambia cuenta en moneda del movimiento no cambia cotización cambia importe
        # Venta de 5 reales en euros, a x reales el euro
        # - Es necesario cambiar la moneda del movimiento a reales
        # - Se calcula cotización x (euro.cotizacion_en(real))
        # - Cambia importe_ce (5 / cotización x)
        # - Cambia importe_cs (5)
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_tercera_moneda_e_importe_se_recalcula_cotizacion_y_se_guarda_importe_ingresado(
                self, sentido, cuenta_con_saldo_en_reales, real, euro, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.importe = 5
            movimiento.full_clean()
            movimiento.save()


            assert movimiento.cotizacion == euro.cotizacion_en_al(real, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 5
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == round(5/movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == 5

        # Cambia cuenta en otra moneda no cambia cotización no cambia importe
        # Venta de 10 dólares en reales, a y dólares el real
        # - Se calcula cotización y (real.cotizacion_en(dolar))
        # - Cambia importe_ce (10 / cotizacion y)
        # - No cambia importe_cs
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_una_tercera_moneda_se_recalculan_cotizacion_e_importe(
                self, sentido, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            importe = movimiento.importe
            importe_cta_en_moneda_mov = getattr(movimiento, f"importe_cta_{sentido}")

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda() is False
            assert movimiento.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) is True
            movimiento.full_clean()
            movimiento.save()

            assert \
                movimiento.cotizacion == \
                real.cotizacion_en_al(movimiento.moneda, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == importe
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == round(importe / movimiento.cotizacion, 2)
            assert getattr(movimiento, f"importe_cta_{sentido}") == importe_cta_en_moneda_mov

        # Cambia cuenta en otra moneda cambia cotización no cambia importe
        # Venta de 10 dólares en reales, a 0,2 dólares el real
        # - Se guarda cotización ingresada
        # - Cambia importe_ce (10 / 0,2)
        # - No cambia importe_cs
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_una_tercera_moneda_y_cotizacion_se_guarda_cotizacion_ingresada_y_se_recalcula_importe(
                self, sentido, cuenta_con_saldo_en_reales, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            importe = movimiento.importe
            importe_cuenta_en_mon_mov = getattr(movimiento, f"importe_cta_{sentido}")

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            movimiento.cotizacion = 0.2
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 0.2
            assert movimiento.importe == importe
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == importe / 0.2
            assert getattr(movimiento, f"importe_cta_{sentido}") == importe_cuenta_en_mon_mov

        # Cambia cuenta en otra moneda cambia cotización cambia importe
        # Venta de 5 dólares en reales, a 0,2 dólares el real
        # - Cambia importe_ce (5 / 0,2)
        # - Cambia importe_cs (5)
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_una_tercera_moneda_cotizacion_e_importe_se_guardan_los_valores_ingresados(
                self, sentido, cuenta_con_saldo_en_reales, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            movimiento.cotizacion = 0.2
            movimiento.importe = 5
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 0.2
            assert movimiento.importe == 5
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == round(5/0.2, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == 5

        # Cambia cuenta en otra moneda no cambia cotización cambia importe
        # Venta de 5 dólares en reales, a x dólares el real
        # - Se calcula cotización x (real.cotizacion_en(dolar))
        # - Cambia importe_ce (5 / cotizacion x)
        # - Cambia importe_cs (5)
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_una_tercera_moneda_e_importe_se_recalcula_cotizacion_y_se_guarda_importe_ingresado(
                self, sentido, cuenta_con_saldo_en_reales, real, dolar, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            movimiento.importe = 5
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == real.cotizacion_en_al(dolar, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 5
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == round(5 / movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == 5

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda no cambia cotización no cambia importe
        # Cambia moneda por moneda de cuenta que reemplaza a cuenta en moneda del movimiento
        # Venta de x reales en yenes, a x reales el yen
        # - Se calcula cotización x (yen.cotizacion_en(real))
        # - Cambia importe_cs (importe / cotización x)
        def test_si_cambian_ambas_cuentas_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_moneda_del_movimiento_se_recalcula_cotizacion(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = yen
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == real.cotizacion_en_al(yen, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == importe
            assert \
                abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == \
                round(movimiento.importe / movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == movimiento.importe

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda no cambia cotización no cambia importe
        # Cambia moneda por moneda de cuenta que reemplaza a cuenta en otra moneda
        # Venta de x reales en yenes, a x yenes el real
        # - Se calcula cotización x (real.cotizacion_en(yen))
        # - Cambia importe_ce (importe / cotizacion x)
        def test_si_cambian_ambas_cuentas_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_otra_moneda_se_recalcula_cotizacion(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido_otra_cuenta == "entrada"

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = real
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == yen.cotizacion_en_al(real, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == importe
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == movimiento.importe
            assert \
                abs(getattr(movimiento, f"importe_cta_{sentido}")) == \
                round(movimiento.importe / movimiento.cotizacion, 2)

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda no cambia cotización cambia importe
        # Cambia moneda por moneda de cuenta que reemplaza a cuenta en moneda del movimiento
        # Venta de 8 reales en yenes, a x yenes el real
        def test_si_cambian_ambas_cuentas_importe_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_moneda_del_movimiento_se_recalcula_cotizacion(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = yen
            movimiento.importe = 8
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == real.cotizacion_en_al(yen, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 8
            assert \
                abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == \
                round(movimiento.importe / movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == 8

        # Cambia cuenta en moneda del movimiento cambia cuenta en otra moneda no cambia cotización cambia importe
        # Cambia moneda por moneda de cuenta que reemplaza a cuenta en otra moneda
        # Venta de 8 reales en yenes, a x reales el yen
        def test_si_cambian_ambas_cuentas_importe_y_moneda_por_moneda_de_cuenta_que_reemplaza_a_cuenta_en_otra_moneda_se_recalcula_cotizacion(
                self, sentido, cuenta_con_saldo_en_reales, cuenta_con_saldo_en_yenes, real, yen, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido_otra_cuenta == "entrada"

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_reales)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_yenes)
            movimiento.moneda = real
            movimiento.importe = 8
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == yen.cotizacion_en_al(real, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 8
            assert \
                abs(getattr(movimiento, f"importe_cta_{sentido}")) == \
                round(movimiento.importe / movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == 8

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
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == importe
            assert \
                abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == \
                round(movimiento.importe / movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == movimiento.importe

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
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == importe
            assert \
                abs(getattr(movimiento, f"importe_cta_{sentido}")) == \
                round(movimiento.importe / movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == movimiento.importe

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
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == 8
            assert \
                abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == \
                round(movimiento.importe / movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == movimiento.importe

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
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == 8
            assert \
                abs(getattr(movimiento, f"importe_cta_{sentido}")) == \
                round(movimiento.importe / movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == movimiento.importe

        def test_si_cambian_ambas_cuentas_cotizacion_e_importe_se_guardan_valores_ingresados(
                self, sentido, cuenta_con_saldo_en_yenes, cuenta_con_saldo_en_reales, real, request):
            movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_otra_cuenta}", cuenta_con_saldo_en_yenes)
            setattr(movimiento, f"cta_{sentido}", cuenta_con_saldo_en_reales)
            movimiento.moneda = real
            movimiento.cotizacion = 3
            movimiento.importe = 8
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 3
            assert movimiento.importe == 8
            assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == round(8/3, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == 8

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # no cambia moneda, no cambia cotización, no cambia importe
        # 10 Dolares->CA dolares pasa a 10 Dolares-> x Euros a y dólares el euro
        # - Se calcula cotización (euro.cotizacion_en(dolar))
        # - Cambia importe_ce (10 / cotización)
        # - No cambia importe_cs
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_se_calcula_cotizacion(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            importe = traspaso_en_dolares.importe
            compra = sentido_otra_cuenta == "entrada"

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.full_clean()
            traspaso_en_dolares.save()

            assert \
                traspaso_en_dolares.cotizacion == \
                euro.cotizacion_en_al(dolar, fecha=traspaso_en_dolares.fecha, compra=compra)
            assert traspaso_en_dolares.importe == importe
            assert \
                abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido_otra_cuenta}")) == \
                traspaso_en_dolares.importe
            assert \
                abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido}")) == \
                round(traspaso_en_dolares.importe / traspaso_en_dolares.cotizacion, 2)

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # no cambia moneda, cambia cotización, no cambia importe
        # 10 Dolares->CA dolares pasa a 10 Dolares-> x Euros a 2 dólares el euro
        # - Cambia importe_ce (10 / 2)
        # - No cambia importe_cs
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_y_cotizacion_se_guarda_cotizacion(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            importe = traspaso_en_dolares.importe

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.cotizacion = 2
            traspaso_en_dolares.full_clean()
            traspaso_en_dolares.save()

            assert traspaso_en_dolares.cotizacion == 2
            assert traspaso_en_dolares.importe == importe
            assert abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido_otra_cuenta}")) == traspaso_en_dolares.importe
            assert \
                abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido}")) == \
                round(traspaso_en_dolares.importe / 2, 2)

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # cambia moneda, no cambia cotización, no cambia importe
        # 10 Dólares->CA dólares pasa a 10 Dólares -> x Euros a y euros el dólar
        # - Se calcula cotización y (dolar.cotizacion_en(euro))
        # - Se calcula importe (10 * cotización y)
        # - Cambia importe_ce (importe)
        # - No cambia importe_cs
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_y_moneda_se_calcula_cotizacion_e_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"
            importe = traspaso_en_dolares.importe

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.moneda = euro
            traspaso_en_dolares.full_clean()
            traspaso_en_dolares.save()

            assert \
                traspaso_en_dolares.cotizacion == \
                dolar.cotizacion_en_al(euro, fecha=traspaso_en_dolares.fecha, compra=compra)
            assert traspaso_en_dolares.importe == round(importe * traspaso_en_dolares.cotizacion, 2)
            assert abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido}")) == traspaso_en_dolares.importe
            assert abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido_otra_cuenta}")) == importe

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # no cambia moneda, no cambia cotización, cambia importe
        # 10 Dólares->CA dólares pasa a 6 Dólares -> x Euros a y dólares el euro
        # - Se calcula cotización (euro.cotizacion_en(dolar)
        # - Cambia importe_ce (6 / cotizacion)
        # - Cambia importe_cs (6)
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_e_importe_se_calcula_cotizacion_y_se_guarda_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido_otra_cuenta == "entrada"

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.importe = 6
            traspaso_en_dolares.full_clean()
            traspaso_en_dolares.save()

            assert \
                traspaso_en_dolares.cotizacion == \
                euro.cotizacion_en_al(dolar, fecha=traspaso_en_dolares.fecha, compra=compra)
            assert traspaso_en_dolares.importe == 6
            assert \
                abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido}")) == \
                round(6 / traspaso_en_dolares.cotizacion, 2)
            assert abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido_otra_cuenta}")) == 6

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # cambia moneda, cambia cotización, no cambia importe
        # 10 Dólares->CA dólares pasa a 10 Dólares -> x Euros a 2 euros el dólar
        # - Se calcula importe (10 * 2)
        # - Cambia importe_ce (10/2)
        # - No cambia importe_cs
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_moneda_y_cotizacion_se_guarda_cotizacion_y_se_calcula_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            importe = traspaso_en_dolares.importe

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.cotizacion = 2
            traspaso_en_dolares.moneda = euro
            traspaso_en_dolares.full_clean()
            traspaso_en_dolares.save()

            assert traspaso_en_dolares.cotizacion == 2
            assert traspaso_en_dolares.importe == importe * 2
            assert \
                abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido}")) == traspaso_en_dolares.importe
            assert abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido_otra_cuenta}")) == importe

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # cambia moneda, no cambia cotización, cambia importe
        # 10 Dólares->CA dólares pasa a 10 Dólares -> 6 Euros a x euros el dólar
        # - Se calcula cotización (dolar.cotizacion_en(euro))
        # - Cambia importe_ce (6)
        # - Cambia importe_cs (6 / cotizacion)
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_moneda_e_importe_se_calcula_cotizacion_y_se_guarda_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.importe = 6
            traspaso_en_dolares.moneda = euro
            traspaso_en_dolares.full_clean()
            traspaso_en_dolares.save()

            assert \
                traspaso_en_dolares.cotizacion == \
                dolar.cotizacion_en_al(euro, fecha=traspaso_en_dolares.fecha, compra=compra)
            assert traspaso_en_dolares.importe == 6
            assert \
                abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido}")) == 6
            assert \
                abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido_otra_cuenta}")) == \
                round(6 / traspaso_en_dolares.cotizacion, 2)

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # no cambia moneda, cambia cotización, cambia importe
        # 10 Dólares->CA dólares pasa a 6 Dólares -> x Euros a 0.6 dólares el euro
        # - Se calcula cotización (euro.cotizacion_en(dolar))
        # - Cambia importe_ce (6 / cotización)
        # - Cambia importe_cs (6)
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_cotizacion_e_importe_se_guardan_cotizacion_e_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.importe = 6
            traspaso_en_dolares.cotizacion = 0.6
            traspaso_en_dolares.full_clean()
            traspaso_en_dolares.save()

            assert traspaso_en_dolares.cotizacion == 0.6
            assert traspaso_en_dolares.importe == 6
            assert \
                abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido}")) == round(6 / 0.6, 2)
            assert abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido_otra_cuenta}")) == 6

        # Entre cuentas en la misma moneda, cambia cuenta por cuenta en otra moneda,
        # cambia moneda, cambia cotización, cambia importe
        # 10 Dólares->CA dólares pasa a x Dólares -> 6 Euros a 0.6 euros el dólar
        # - Cambia importe_ce (6)
        # - Cambia importe_cs (6 / cotización)
        def test_si_en_traspaso_entre_cuentas_en_la_misma_moneda_cambia_cuenta_por_cuenta_en_otra_moneda_moneda_cotizacion_e_importe_se_guardan_cotizacion_e_importe(
                self, sentido, traspaso_en_dolares, cuenta_con_saldo_en_euros, euro, dolar):
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(traspaso_en_dolares, f"cta_{sentido}", cuenta_con_saldo_en_euros)
            traspaso_en_dolares.importe = 6
            traspaso_en_dolares.cotizacion = 0.6
            traspaso_en_dolares.moneda = euro
            traspaso_en_dolares.full_clean()
            traspaso_en_dolares.save()

            assert traspaso_en_dolares.cotizacion == 0.6
            assert traspaso_en_dolares.importe == 6
            assert \
                abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido}")) == 6
            assert abs(getattr(traspaso_en_dolares, f"importe_cta_{sentido_otra_cuenta}")) == round(6 / 0.6, 2)

        # Entre cuentas en distinta moneda, cambia cuenta en otra moneda por cuenta en moneda del movimiento,
        # no cambia importe
        # 10 dolares -> x euros a 1.5 dólares el euro  pasa a  10 dólares -> CA dólares
        # - Cambia cotización (1)
        # - Cambia importe_ce (importe)
        # - No cambia importe_cs
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_moneda_del_movimiento_cotizacion_pasa_a_1(
                self, sentido, cuenta_en_dolares, request):
            mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
            importe = mov_distintas_monedas.importe

            setattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}", cuenta_en_dolares)
            mov_distintas_monedas.full_clean()
            mov_distintas_monedas.save()

            assert mov_distintas_monedas.cotizacion == 1
            assert mov_distintas_monedas.importe == importe
            assert mov_distintas_monedas.importe_cta_entrada == mov_distintas_monedas.importe
            assert mov_distintas_monedas.importe_cta_salida == -mov_distintas_monedas.importe

        # Entre cuentas en distinta moneda, cambia cuenta en otra moneda por cuenta en moneda del movimiento,
        # cambia importe
        # 10 dolares -> x euros a 1.5 dólares el euro  pasa a  6 dólares -> CA dólares
        # - Cambia cotización (1)
        # - Cambia importe_ce (6)
        # - Cambia importe_cs (6)
        def test_si_cambia_cuenta_en_moneda_no_del_movimiento_por_cuenta_en_moneda_del_movimiento_e_importe_se_guarda_importe_y_cotizacion_pasa_a_1(
                self, sentido, cuenta_en_dolares, request):
            mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}", cuenta_en_dolares)
            mov_distintas_monedas.importe = 6
            mov_distintas_monedas.full_clean()
            mov_distintas_monedas.save()

            assert mov_distintas_monedas.cotizacion == 1
            assert mov_distintas_monedas.importe == 6
            assert mov_distintas_monedas.importe_cta_entrada == 6
            assert mov_distintas_monedas.importe_cta_salida == -6

        # Entre cuentas en distinta moneda, cambia cuenta en moneda del movimiento por cuenta en otra moneda,
        # no cambia importe
        # 10 dolares -> x euros a 1.5 dólares el euro  pasa a  CA euros -> x euros
        # - Cambia cotización (1)
        # - Cambia importe_ce(10 / 1.5)
        # - Cambia importe_cs(10 / 1.5)
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_moneda_no_del_movimiento_se_calcula_importe_y_cotizacion_pasa_a_1(
                self, sentido, cuenta_en_euros, euro, request):
            mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
            cotizacion = mov_distintas_monedas.cotizacion
            importe = mov_distintas_monedas.importe

            setattr(mov_distintas_monedas, f"cta_{sentido}", cuenta_en_euros)
            mov_distintas_monedas.moneda = euro
            mov_distintas_monedas.full_clean()
            mov_distintas_monedas.save()

            assert mov_distintas_monedas.cotizacion == 1
            assert mov_distintas_monedas.importe == round(importe / cotizacion, 2)
            assert mov_distintas_monedas.importe_cta_entrada == mov_distintas_monedas.importe
            assert mov_distintas_monedas.importe_cta_salida == -mov_distintas_monedas.importe

        # Entre cuentas en distinta moneda, cambia cuenta en moneda del movimiento por cuenta en otra moneda,
        # cambia importe
        # 10 dolares -> x euros a 1.5 dólares el euro  pasa a  CA euros -> 6 euros
        # - Cambia cotización (1)
        # - Cambia importe_ce(6)
        # - Cambia importe_cs(6)
        def test_si_cambia_cuenta_en_moneda_del_movimiento_por_cuenta_en_moneda_no_del_movimiento_e_importe_se_guarda_importe_y_cotizacion_pasa_a_1(
                self, sentido, cuenta_en_euros, euro, request):
            mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")

            setattr(mov_distintas_monedas, f"cta_{sentido}", cuenta_en_euros)
            mov_distintas_monedas.moneda = euro
            mov_distintas_monedas.importe = 6
            mov_distintas_monedas.full_clean()
            mov_distintas_monedas.save()

            assert mov_distintas_monedas.cotizacion == 1
            assert mov_distintas_monedas.importe == 6
            assert mov_distintas_monedas.importe_cta_entrada == 6
            assert mov_distintas_monedas.importe_cta_salida == -6

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # no cambia moneda, no cambia cotización, no cambia importe.
        # Entran / salen 10 dólares -> Venta / compra de 10 dólares de euros
        # - No cambia importe
        # - Cambia cotización (euro.cotizacion_en(dolar))
        # - No cambia importe_ce/cs
        # - Cambia importe_cs/ce (importe / nueva cotización)
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_se_calcula_cotizacion(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == euro.cotizacion_en_al(dolar, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == importe
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == importe
            assert \
                abs(getattr(movimiento, f"importe_cta_{sentido_contracuenta}")) == \
                round(importe / movimiento.cotizacion, 2)

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # no cambia moneda, cambia cotización, no cambia importe.
        # Entran / salen 10 dólares -> Venta / compra de 10 dólares de euros a 1.5 dólares el euro
        # - No cambia importe
        # - Cambia cotización (1.5)
        # - No cambia importe_ce/cs
        # - Cambia importe_cs/ce (importe / 1.5)
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cotizacion_se_guarda_cotizacion_ingresada(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.cotizacion = 1.5
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 1.5
            assert movimiento.importe == importe
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == importe
            assert abs(getattr(movimiento, f"importe_cta_{sentido_contracuenta}")) == round(importe / 1.5, 2)

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # no cambia moneda, no cambia cotización, cambia importe.
        # Entran / salen 10 dólares -> Venta / compra de 20 dólares de euros
        # - Cambia importe (20)
        # - Cambia cotización (euro.cotizacion_en(dolar))
        # - Cambia importe_ce/cs (20)
        # - Cambia importe_cs/ce (20 / nueva cotizacion)
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_se_ingresa_importe_se_calcula_cotizacion_y_se_guarda_importe_ingresado(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.importe = 20
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == euro.cotizacion_en_al(dolar, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 20
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == 20
            assert abs(getattr(movimiento, f"importe_cta_{sentido_contracuenta}")) == round(20 / movimiento.cotizacion, 2)

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # no cambia moneda, cambia cotización, cambia importe.
        # Entran / salen 10 dólares -> Venta / compra de 20 dólares de euros a 1.5 dólares el euro
        # - Cambia importe (20)
        # - Cambia cotización (1.5)
        # - Cambia importe_ce/cs (20)
        # - Cambia importe_cs/ce (20 / 1.5)
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_se_ingresa_cotizacion_e_importe_se_guardan_valores_ingresados(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.cotizacion = 1.5
            movimiento.importe = 20
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 1.5
            assert movimiento.importe == 20
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == 20
            assert abs(getattr(movimiento, f"importe_cta_{sentido_contracuenta}")) == round(20 / 1.5, 2)

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # cambia moneda, no cambia cotización, no cambia importe.
        # Entran / salen 10 dólares -> Venta / compra de x euros de dólares a y euros el dólar
        # - Cambia cotización (dolar.cotizacion_en(euro))
        # - Cambia importe (10 * nueva cotizacion)
        # - No cambia importe_ce/cs
        # - Cambia importe_cs/ce (nuevo importe)
        @pytest.mark.xfail
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cambia_moneda_se_calcula_cotizacion_e_importe(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido == "entrada"

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.moneda = euro
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == euro.cotizacion_en_al(euro, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == round(importe * movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == importe
            assert abs(getattr(movimiento, f"importe_cta:{sentido_contracuenta}")) == movimiento.importe

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # cambia moneda, cambia cotización, no cambia importe.
        # Entran / salen 10 dólares -> Venta / compra de x euros de dólares a 0.8 euros el dólar
        # - Cambia cotización (0.8)
        # - Cambia importe (10 * 0.8)
        # - No cambia importe_ce/cs
        # - Cambia importe_cs/ce (nuevo importe)
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cambia_moneda_y_cotizacion_se_guarda_cotizacion_y_se_calcula_importe(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")

            importe = movimiento.importe

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.moneda = euro
            movimiento.cotizacion = 0.8
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 0.8
            assert movimiento.importe == round(importe * 0.8, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == importe
            assert abs(getattr(movimiento, f"importe_cta_{sentido_contracuenta}")) == movimiento.importe

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # cambia moneda, no cambia cotización, cambia importe.
        # Entran / salen 10 dólares -> Venta / compra de 20 euros de dólares a x euros el dólar
        # - Cambia cotización (dolar.cotizacion_en(euro))
        # - Cambia importe (20)
        # - Cambia importe_ce/cs (20 / nueva cotización)
        # - Cambia importe_cs/ce (20)
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cambia_moneda_e_importe_se_calcula_cotizacion_y_se_guarda_importe(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")
            compra = sentido_contracuenta == "entrada"

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.moneda = euro
            movimiento.importe = 20
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == dolar.cotizacion_en_al(euro, fecha=movimiento.fecha, compra=compra)
            assert movimiento.importe == 20
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == round(20 / movimiento.cotizacion, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido_contracuenta}")) == 20

        # En movimiento de entrada/salida, se agrega cuenta de salida/entrada en otra moneda,
        # cambia moneda, cambia cotización, cambia importe.
        # Entran / salen 10 dólares -> Venta / compra de 20 euros de dólares a 0.8 euros el dólar
        # - Cambia cotización (0.8)
        # - Cambia importe (20)
        # - Cambia importe_ce/cs (20 / 0.8)
        # - Cambia importe_cs/ce (20)
        def test_si_en_movimiento_de_entrada_o_salida_se_agrega_contracuenta_en_otra_moneda_y_cambia_moneda_cotizacion_e_importe_se_guardan_cotizacion_e_importe(
                self, sentido, cuenta_en_euros, dolar, euro, request):
            movimiento = request.getfixturevalue(f"{sentido}_en_dolares")
            sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")

            setattr(movimiento, f"cta_{sentido_contracuenta}", cuenta_en_euros)
            movimiento.moneda = euro
            movimiento.cotizacion = 0.8
            movimiento.importe = 20
            movimiento.full_clean()
            movimiento.save()

            assert movimiento.cotizacion == 0.8
            assert movimiento.importe == 20
            assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == round(20 / 0.8, 2)
            assert abs(getattr(movimiento, f"importe_cta_{sentido_contracuenta}")) == 20

        def test_puede_agregarse_cuenta_interactiva_a_movimiento_con_cta_acumulativa(
                self, sentido, cuenta_2, request):
            mov = request.getfixturevalue(f'{sentido}_con_ca')
            contrasentido = 'entrada' if sentido == 'salida' else 'salida'

            setattr(mov, f'cta_{contrasentido}', cuenta_2)
            mov.full_clean()
            mov.save()

            assert getattr(mov, f'cta_{contrasentido}') == cuenta_2

        def test_puede_cambiarse_cta_interactiva_en_movimiento_con_cuenta_acumulativa(
                self, sentido, cuenta_3, request):
            mov = request.getfixturevalue(f'traspaso_con_cta_{sentido}_a')
            contrasentido = 'entrada' if sentido == 'salida' else 'salida'

            setattr(mov, f'cta_{contrasentido}', cuenta_3)
            mov.full_clean()
            mov.save()

            assert getattr(mov, f'cta_{contrasentido}') == cuenta_3

        def test_puede_retirarse_cta_interactiva_en_movimiento_con_cta_entrada_acumulativa(
                self, sentido, request):
            mov = request.getfixturevalue(f'traspaso_con_cta_{sentido}_a')
            contrasentido = 'entrada' if sentido == 'salida' else 'salida'

            setattr(mov, f'cta_{contrasentido}', None)
            mov.full_clean()
            mov.save()

            assert getattr(mov, f'cta_{contrasentido}') is None


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaImporteYCuentas:
    def test_si_cambia_cuenta_e_importe_desaparece_saldo_en_movimiento_de_cuenta_anterior_y_aparece_el_de_la_nueva_con_el_nuevo_importe(
            self, sentido, cuenta_2, importe_aleatorio, request):
        mov, s, cuenta_anterior = inferir_fixtures(sentido, request)
        cant_saldos = cuenta_2.saldo_set.count()

        setattr(mov, f'cta_{sentido}', cuenta_2)
        mov.importe = importe_aleatorio
        mov.save()

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta_anterior, movimiento=mov)
        assert cuenta_2.saldo_set.count() == cant_saldos + 1
        assert cuenta_2.saldo_en_mov(mov) == s * importe_aleatorio

    def test_si_cambia_cuenta_e_importe_en_mov_de_traspaso_desaparece_saldo_en_movimiento_de_cuenta_anterior_y_aparece_el_de_la_nueva_con_el_nuevo_importe_y_se_actualiza_importe_de_la_cuenta_no_cambiada(
            self, sentido, traspaso, cuenta_3, importe_aleatorio):
        s = signo(sentido == 'entrada')
        contrasentido = 'salida' if sentido == 'entrada' else 'entrada'
        cuenta_anterior = getattr(traspaso, f'cta_{sentido}')
        cuenta_no_cambiada = getattr(traspaso, f'cta_{contrasentido}')
        importe_anterior = traspaso.importe
        saldo_anterior_cuenta_no_cambiada = cuenta_no_cambiada.saldo_en_mov(traspaso)
        cant_saldos = cuenta_3.saldo_set.count()

        setattr(traspaso, f'cta_{sentido}', cuenta_3)
        traspaso.importe = importe_aleatorio
        traspaso.save()

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta_anterior, movimiento=traspaso)
        assert cuenta_3.saldo_set.count() == cant_saldos + 1
        assert cuenta_3.saldo_en_mov(traspaso) == s * importe_aleatorio
        assert \
            cuenta_no_cambiada.saldo_en_mov(traspaso) == \
            approx(
                saldo_anterior_cuenta_no_cambiada +
                s * importe_anterior -
                s * importe_aleatorio
            )


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

        assert cuenta.saldo_en_mov(salida_posterior) == saldo_intermedio - s * mov.importe

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
        cambiar_fecha_creacion(cuenta, fecha_temprana)
        saldo_anterior = cuenta.saldo_en_mov(entrada_anterior)

        cambiar_fecha(mov, fecha_temprana)

        assert cuenta.saldo_en_mov(entrada_anterior) == saldo_anterior + s * mov.importe

    def test_si_cambia_fecha_a_una_fecha_anterior_suma_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cuenta(
            self, sentido, entrada_temprana, entrada_anterior, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        cambiar_fecha_creacion(cuenta, entrada_temprana.fecha)
        cambiar_fecha(mov, entrada_temprana.fecha + timedelta(1))

        assert cuenta.saldo_en_mov(mov) == cuenta.saldo_en_mov(entrada_temprana) + s * mov.importe

    def test_si_cambia_fecha_a_una_fecha_anterior_y_no_hay_saldo_anterior_de_cuenta_asigna_importe_del_movimiento_a_saldo_de_cuenta_en_nueva_ubicacion_del_movimiento(
            self, sentido, fecha_temprana, entrada_anterior, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        cambiar_fecha_creacion(cuenta, fecha_temprana)
        cambiar_fecha(mov, fecha_temprana)

        assert cuenta.saldo_en_mov(mov) == s * mov.importe

    def test_si_cambia_fecha_a_una_fecha_anterior_no_modifica_importes_de_saldos_de_cuenta_anteriores_a_nueva_ubicacion_de_movimiento(
            self, sentido, entrada_temprana, entrada_anterior, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        saldo_temprano = cuenta.saldo_en_mov(entrada_temprana)

        cambiar_fecha(mov, entrada_anterior.fecha)

        assert cuenta.saldo_en_mov(entrada_temprana) == saldo_temprano

    def test_si_cambia_fecha_a_una_fecha_anterior_no_modifica_importes_de_saldos_de_cta_entrada_posteriores_a_ubicacion_anterior_de_movimiento(
            self, sentido, entrada_anterior, salida_posterior, fecha_temprana, request):
        mov, _, cuenta = inferir_fixtures(sentido, request)
        cambiar_fecha_creacion(cuenta, fecha_temprana)
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

        assert cuenta.saldo_en_mov(traspaso) == saldo_traspaso - s * mov.importe

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

        assert cuenta.saldo_en_mov(entrada_otra_cuenta) == saldo_entrada_otra_cuenta + s * mov.importe

    def test_si_cambia_orden_dia_a_un_orden_anterior_suma_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cuenta(
            self, sentido, traspaso, entrada_otra_cuenta, entrada, salida, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)

        cambiar_orden(mov, 1)

        assert cuenta.saldo_en_mov(mov) == cuenta.saldo_en_mov(traspaso) + s * mov.importe

    def test_si_cambia_orden_dia_a_un_orden_anterior_y_no_hay_saldo_anterior_de_cta_entrada_asigna_importe_del_movimiento_a_saldo_de_cuenta_en_nueva_ubicacion_del_movimiento(
            self, sentido, traspaso, entrada_otra_cuenta, entrada, salida, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)

        cambiar_orden(mov, 0)

        assert cuenta.saldo_en_mov(mov) == s * mov.importe

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


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaFechaYOrdenDia:

    @pytest.mark.parametrize('_otro_mov, otro_orden', [
        ('salida_posterior', 1),
        ('entrada_anterior', 0),
    ])
    def test_si_cambia_fecha_y_orden_dia_a_modifica_saldos_intermedios_de_cuenta(
            self, sentido, _otro_mov, otro_orden, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        otro_mov = request.getfixturevalue(_otro_mov)
        s2 = signo(_otro_mov == 'entrada_anterior')

        saldo_otro_mov = cuenta.saldo_en_mov(otro_mov)

        mov.fecha = otro_mov.fecha
        mov.orden_dia = otro_orden
        mov.full_clean()
        mov.save(mantiene_orden_dia=True)

        otro_mov.refresh_from_db(fields=['orden_dia'])

        assert \
            cuenta.saldo_en_mov(otro_mov) == \
            saldo_otro_mov + s * s2 * mov.importe


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaImporteYFecha:

    @pytest.mark.parametrize('_otro_mov', [
        'salida_posterior',
        'entrada_anterior',
    ])
    def test_si_cambia_importe_y_fecha_resta_o_suma_importe_viejo_a_saldos_intermedios_de_cuenta_entre_antigua_y_nueva_posicion(
            self, sentido, _otro_mov, entrada_temprana, importe_aleatorio, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        otro_mov = request.getfixturevalue(_otro_mov)
        s2 = signo(_otro_mov == 'entrada_anterior')
        saldo_otro_mov = cuenta.saldo_en_mov(otro_mov)
        # si pasa a fecha posterior, resta/suma importe nuevo
        # si pasa a fecha anterior, resta/suma importe original
        importe = mov.importe if _otro_mov == 'salida_posterior' else importe_aleatorio
        cambiar_fecha_creacion(cuenta, entrada_temprana.fecha)

        mov.fecha = otro_mov.fecha - s2 * timedelta(1)
        mov.importe = importe_aleatorio
        mov.full_clean()
        mov.save()

        assert cuenta.saldo_en_mov(otro_mov) == pytest.approx(saldo_otro_mov + s * s2 * importe, 0.02)

    @pytest.mark.parametrize('_otro_mov', [
        'salida_posterior',
        'entrada_anterior',
    ])
    def test_si_cambia_importe_y_fecha_resta_o_suma_importe_nuevo_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cuenta(
            self, sentido, _otro_mov, entrada_temprana, importe_aleatorio, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        otro_mov = request.getfixturevalue(_otro_mov)
        cambiar_fecha_creacion(cuenta, entrada_temprana.fecha)
        mov_anterior = otro_mov if _otro_mov == 'salida_posterior' else entrada_temprana
        s2 = signo(_otro_mov == 'salida_posterior')

        mov.fecha = otro_mov.fecha + s2 * timedelta(1)
        mov.importe = importe_aleatorio
        mov.full_clean()
        mov.save()

        assert cuenta.saldo_en_mov(mov) == approx(
            cuenta.saldo_en_mov(mov_anterior) + s * importe_aleatorio
        )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaImporteYOrdenDia:

    def test_si_cambia_importe_y_orden_dia_a_un_orden_posterior_resta_importe_viejo_de_saldos_intermedios_de_cuenta(
            self, sentido, entrada, salida, traspaso, entrada_otra_cuenta, importe_aleatorio, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_traspaso = cuenta.saldo_en_mov(traspaso)
        importe = mov.importe

        mov.importe = importe_aleatorio
        mov.orden_dia = traspaso.orden_dia + 1
        mov.full_clean()
        mov.save()

        assert cuenta.saldo_en_mov(traspaso) == saldo_traspaso - s * importe

    def test_si_cambia_importe_y_orden_dia_a_un_orden_posterior_suma_importe_nuevo_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_entrada(
            self, sentido, entrada, salida, traspaso, entrada_otra_cuenta, importe_aleatorio, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)

        mov.importe = importe_aleatorio
        mov.orden_dia = traspaso.orden_dia + 1
        mov.full_clean()
        mov.save()

        assert \
            cuenta.saldo_en_mov(mov), 2 == \
                                      approx(cuenta.saldo_en_mov(traspaso) + s * importe_aleatorio)

    def test_si_cambia_orden_dia_a_un_orden_anterior_suma_importe_nuevo_a_saldos_intermedios_de_cuenta(
            self, sentido, traspaso, entrada_otra_cuenta, entrada, salida, importe_aleatorio, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_entrada_otra_cuenta = cuenta.saldo_en_mov(entrada_otra_cuenta)

        mov.importe = importe_aleatorio
        mov.orden_dia = entrada_otra_cuenta.orden_dia - 1
        mov.full_clean()
        mov.save()
        traspaso.refresh_from_db()
        entrada_otra_cuenta.refresh_from_db()

        assert \
            cuenta.saldo_en_mov(entrada_otra_cuenta) == \
            approx(saldo_entrada_otra_cuenta + s * importe_aleatorio)

    def test_si_cambia_importe_y_orden_dia_a_un_orden_anterior_suma_importe_nuevo_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_entrada(
            self, sentido, traspaso, entrada_otra_cuenta, entrada, salida, importe_aleatorio, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)

        mov.importe = importe_aleatorio
        mov.orden_dia = entrada_otra_cuenta.orden_dia
        mov.full_clean()
        mov.save()

        assert cuenta.saldo_en_mov(mov) == approx(
            cuenta.saldo_en_mov(traspaso) + s * importe_aleatorio
        )


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
class TestSaveCambiaCuentasYFecha:
    def test_si_cambia_cuenta_y_fecha_a_posterior_resta_importe_a_saldos_de_vieja_cuenta_posteriores_a_antigua_posicion_de_movimiento(
            self, sentido, cuenta_2, salida_posterior, entrada_tardia, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_posterior = cuenta.saldo_en_mov(salida_posterior)

        setattr(mov, f'cta_{sentido}', cuenta_2)
        mov.fecha = salida_posterior.fecha + timedelta(1)
        mov.full_clean()
        mov.save()

        assert cuenta.saldo_en_mov(salida_posterior) == saldo_posterior - s * mov.importe

    def test_si_cambia_cta_entrada_y_fecha_a_posterior_suma_importe_a_saldos_de_cuenta_nueva_a_partir_de_nueva_ubicacion_del_movimiento(
            self, sentido, cuenta_2, salida_posterior, entrada_tardia, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_tardio = cuenta_2.saldo_en_mov(entrada_tardia)

        setattr(mov, f'cta_{sentido}', cuenta_2)
        mov.fecha = salida_posterior.fecha + timedelta(1)
        mov.full_clean()
        mov.save()

        assert cuenta_2.saldo_en_mov(entrada_tardia) == saldo_tardio + s * mov.importe

    def test_si_cambia_cuenta_y_fecha_a_anterior_saldos_de_vieja_cuenta_posteriores_a_nueva_posicion_del_movimiento_no_cambian(
            self, sentido, cuenta_2, entrada_anterior, entrada_temprana, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        saldo_anterior = cuenta.saldo_en_mov(entrada_anterior)
        cambiar_fecha_creacion(cuenta_2, entrada_temprana.fecha)

        setattr(mov, f'cta_{sentido}', cuenta_2)
        mov.fecha = entrada_anterior.fecha - timedelta(1)
        mov.full_clean()
        mov.save()

        assert cuenta.saldo_en_mov(entrada_anterior) == saldo_anterior

    def test_si_cambia_cta_entrada_y_fecha_a_anterior_suma_importe_solo_a_saldos_de_cuenta_nueva_a_partir_de_nueva_ubicacion_del_movimiento(
            self, sentido, cuenta_2, entrada_anterior, entrada_temprana, request):
        mov, s, cuenta = inferir_fixtures(sentido, request)
        cambiar_fecha_creacion(cuenta_2, entrada_temprana.fecha)
        saldo_anterior = cuenta_2.saldo_en_mov(entrada_anterior)
        saldo_temprano = cuenta_2.saldo_en_mov(entrada_temprana)

        setattr(mov, f'cta_{sentido}', cuenta_2)
        mov.fecha = entrada_anterior.fecha - timedelta(1)
        mov.full_clean()
        mov.save()

        assert cuenta_2.saldo_en_mov(entrada_anterior) == saldo_anterior + s * mov.importe
        assert cuenta_2.saldo_en_mov(entrada_temprana) == saldo_temprano

    def test_si_se_intercambian_cuentas_y_cambia_fecha_a_fecha_posterior_en_un_movimiento_de_traspaso_se_actualizan_correctamente_importes_de_saldo_modificado_e_intermedios(
            self, sentido, traspaso, salida_posterior, entrada_tardia, request):
        cuenta = traspaso.cta_entrada
        cuenta_2 = traspaso.cta_salida
        saldo_posterior_cuenta = cuenta.saldo_en_mov(salida_posterior)
        saldo_posterior_cuenta_2 = cuenta_2.saldo_en_mov(salida_posterior)
        saldo_tardio_cuenta = cuenta.saldo_en_mov(entrada_tardia)
        saldo_tardio_cuenta_2 = cuenta_2.saldo_en_mov(entrada_tardia)

        traspaso.fecha = salida_posterior.fecha + timedelta(1)
        traspaso.cta_entrada, traspaso.cta_salida = cuenta_2, cuenta
        traspaso.full_clean()
        traspaso.save()

        assert cuenta.saldo_en_mov(salida_posterior) == saldo_posterior_cuenta - traspaso.importe
        assert cuenta.saldo_en_mov(traspaso) == cuenta.saldo_en_mov(salida_posterior) - traspaso.importe
        assert cuenta.saldo_en_mov(entrada_tardia) == saldo_tardio_cuenta - traspaso.importe * 2
        assert cuenta_2.saldo_en_mov(salida_posterior) == saldo_posterior_cuenta_2 + traspaso.importe
        assert cuenta_2.saldo_en_mov(traspaso) == cuenta_2.saldo_en_mov(salida_posterior) + traspaso.importe
        assert cuenta_2.saldo_en_mov(entrada_tardia) == saldo_tardio_cuenta_2 + traspaso.importe * 2


class TestSaveCambiaEsGratis:

    def test_mov_esgratis_true_elimina_contramovimiento(self, credito):
        id_contramov = credito.id_contramov
        credito.esgratis = True
        credito.full_clean()
        credito.save()

        with pytest.raises(Movimiento.DoesNotExist):
            Movimiento.tomar(id=id_contramov)

    def test_mov_esgratis_false_genera_contramovimiento(self, donacion):
        donacion.esgratis = False
        donacion.full_clean()
        donacion.save()

        assert donacion.id_contramov is not None
        assert Movimiento.tomar(id=donacion.id_contramov).concepto == "Constitución de crédito"
        assert Movimiento.tomar(id=donacion.id_contramov).detalle == "de Otro Titular a Titular"


class TestSaveCambiaMoneda:

    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_moneda_en_traspaso_entre_cuentas_en_distinta_moneda_no_modifica_saldos_de_cuentas(
            self, sentido, euro, request):
        movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_contracuenta = el_que_no_es(sentido, "entrada", "salida")
        
        ceu = getattr(movimiento, f"cta_{sentido}")
        cdl = getattr(movimiento, f"cta_{sentido_contracuenta}")
        saldo_ceu = ceu.saldo
        saldo_cdl = cdl.saldo

        movimiento.moneda = euro
        movimiento.full_clean()
        movimiento.save()

        ceu.refresh_from_db()
        cdl.refresh_from_db()

        assert ceu.saldo == saldo_ceu
        assert cdl.saldo == saldo_cdl

    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_cotizacion_en_traspaso_entre_cuentas_en_distinta_moneda_impacta_en_saldo_de_cuenta_en_moneda_distinta_de_la_del_movimiento(
            self, sentido, cuenta_con_saldo_en_euros, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
        saldo = getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}").saldo
        print(saldo)
        importe = getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")

        mov_distintas_monedas.cotizacion = 4
        mov_distintas_monedas.full_clean()
        mov_distintas_monedas.save()

        nuevo_importe = getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")
        assert nuevo_importe != importe
        assert \
            getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}").saldo == \
            round(saldo - importe + nuevo_importe, 2)

    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_cotizacion_en_traspaso_entre_cuentas_en_distinta_moneda_cambia_importe_de_cuenta_en_otra_moneda(
            self, sentido, request):
        movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
        importe = abs(getattr(movimiento, f"importe_cta_{sentido}"))

        movimiento.cotizacion = 4
        movimiento.full_clean()
        movimiento.save()

        assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == importe
        assert abs(getattr(movimiento, f"importe_cta_{sentido_otra_cuenta}")) == importe / 4

    # Original: Venta de 10 dólares en euros, a 1,366 dólares el euro
    # - importe_ce: 10 / 1,366
    # - importe_cs: 10

    # Cambia moneda no cambia cotización no cambia importe
    # Compra de x euros en dólares, a y euros el dólar
    # - Se calcula cotización y (1 / cot_vieja)
    # - Se calcula importe x (imp_viejo * cotización)
    # - No cambian importe_ce ni importe_cs
    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_moneda_en_traspaso_entre_cuentas_en_distinta_moneda_se_recalcula_cotizacion_e_importe(
            self, sentido, euro, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        cotizacion = mov_distintas_monedas.cotizacion
        importe = mov_distintas_monedas.importe
        importe_ce = mov_distintas_monedas.importe_cta_entrada
        importe_cs = mov_distintas_monedas.importe_cta_salida

        mov_distintas_monedas.moneda = euro
        mov_distintas_monedas.full_clean()
        mov_distintas_monedas.save()

        assert round(mov_distintas_monedas.cotizacion, 2) == round(1 / cotizacion, 2)
        assert mov_distintas_monedas.importe == round(importe * mov_distintas_monedas.cotizacion, 2)
        assert mov_distintas_monedas.importe_cta_entrada == importe_ce
        assert mov_distintas_monedas.importe_cta_salida == importe_cs

    # Cambia moneda cambia cotización no cambia importe
    # Compra de x euros en dólares, a 0,8 euros el dólar
    # - Se calcula importe x (imp_viejo * cotización)
    # - Cambia importe_ce (importe x)
    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_moneda_y_cotizacion_en_traspaso_entre_cuentas_en_distinta_moneda_toma_cotizacion_pasada_manualmente(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
        otra_cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}")
        importe = mov_distintas_monedas.importe
        cotizacion = mov_distintas_monedas.cotizacion
        importe_otra_cuenta = abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}"))

        mov_distintas_monedas.moneda = otra_cuenta.moneda
        mov_distintas_monedas.cotizacion = 4
        mov_distintas_monedas.full_clean()
        mov_distintas_monedas.save()

        assert mov_distintas_monedas.cotizacion == 4
        assert mov_distintas_monedas.importe == importe * mov_distintas_monedas.cotizacion
        assert abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido}")) == importe
        assert abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")) == importe * 4

    # Cambia moneda cambia cotización cambia importe
    # Compra de 5 euros, a 0,8 euros el dólar
    # - Cambia importe_ce (5)
    # - Cambia importe_cs (5 / 0,8)
    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_moneda_cotizacion_e_importe_cambian_importes_cta_entrada_y_cta_salida(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')
        otra_cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}")

        mov_distintas_monedas.moneda = otra_cuenta.moneda
        mov_distintas_monedas.cotizacion = 4
        mov_distintas_monedas.importe = 5
        mov_distintas_monedas.full_clean()
        mov_distintas_monedas.save()

        assert mov_distintas_monedas.cotizacion == 4
        assert mov_distintas_monedas.importe == 5
        assert abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")) == mov_distintas_monedas.importe
        assert abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido}")) == (5 / 4)

    # Cambia moneda no cambia cotización cambia importe
    # Compra de 5 euros, a x euros el dólar
    # - Se calcula cotización x (1 / cot_vieja)
    # - Cambia importe_ce (5)
    # - Cambia importe_cs (5 / cotización x)
    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_moneda_e_importe_se_recalcula_cotizacion(self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')
        otra_cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}")
        cotizacion = mov_distintas_monedas.cotizacion

        mov_distintas_monedas.moneda = otra_cuenta.moneda
        mov_distintas_monedas.importe = 5
        mov_distintas_monedas.full_clean()
        mov_distintas_monedas.save()

        assert round(mov_distintas_monedas.cotizacion, 2) == round(1 / cotizacion, 2)
        assert mov_distintas_monedas.importe == 5
        assert \
            abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")) == \
            mov_distintas_monedas.importe
        assert \
            abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido}")) == \
            round(5 / mov_distintas_monedas.cotizacion, 2)

    # No cambia moneda cambia cotización no cambia importe
    # Venta de 10 dólares en euros, a 2 dólares el euro
    # - cambia importe_ce (10 / 2)
    # - no cambia importe_cs
    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_cotizacion_en_traspaso_entre_cuentas_en_distinta_moneda_no_cambia_importe_del_movimiento(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')

        # importe_cta_salida = mov_distintas_monedas.importe_cta_salida
        importe = mov_distintas_monedas.importe

        mov_distintas_monedas.cotizacion = 2
        mov_distintas_monedas.full_clean()
        mov_distintas_monedas.save()

        assert mov_distintas_monedas.cotizacion == 2
        assert mov_distintas_monedas.importe == importe
        assert \
            abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")) == \
            mov_distintas_monedas.importe / 2
        assert abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido}")) == importe

    # No cambia moneda cambia cotización cambia importe
    # Venta de 5 dólares en euros, a 2 dólares el euro
    # - Cambia importe_ce (5 / 2)
    # - Cambia importe_cs (5)
    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_cotizacion_e_importe_en_traspaso_entre_cuentas_en_distinta_moneda_se_guardan_valores_ingresados(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')

        mov_distintas_monedas.cotizacion = 2
        mov_distintas_monedas.importe = 25
        mov_distintas_monedas.full_clean()
        mov_distintas_monedas.save()

        assert mov_distintas_monedas.cotizacion == 2
        assert mov_distintas_monedas.importe == 25
        assert abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido}")) == 25
        assert abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")) == 25 / 2

    # No cambia moneda no cambia cotización cambia importe
    # Venta de 5 dólares en euros, a x dólares el euro
    # - Cambia importe_ce (5 / 1,366)
    # - Cambia importe_cs (5)
    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_importe_en_traspaso_entre_cuentas_en_distinta_moneda_se_guarda_importe_y_no_cambia_cotizacion(
            self, sentido, request):
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, 'entrada', 'salida')
        cotizacion = mov_distintas_monedas.cotizacion

        mov_distintas_monedas.importe = 25
        mov_distintas_monedas.full_clean()
        mov_distintas_monedas.save()

        assert mov_distintas_monedas.cotizacion == cotizacion
        assert mov_distintas_monedas.importe == 25
        assert abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido}")) == 25
        assert \
            abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")) == \
            round(25 / mov_distintas_monedas.cotizacion, 2)

        # assert mov_distintas_monedas.importe_cta_entrada == round(25 / mov_distintas_monedas.cotizacion, 2)
        # assert mov_distintas_monedas.importe_cta_salida == -25

    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_moneda_y_cuenta_desaparece_saldo_en_movimiento_de_cuenta_anterior_y_aparece_el_de_la_nueva_con_el_mismo_importe(
            self, sentido, titular, fecha, euro, request):
        """ Si en un movimiento entre cuentas en distinta moneda cambia la moneda
            y a la vez se reemplaza una de las cuentas por otra en la misma moneda,
            desaparece el saldo asociado a la cuenta reemplazada y el movimiento
            y aparece un nuevo saldo en la cuenta reemplazante calculado sobre el mismo importe.
        """
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")
        cuenta_cambiada = getattr(mov_distintas_monedas, f"cta_{sentido}")
        otra_cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}")

        cuenta_en_la_misma_moneda = Cuenta.crear(
            nombre='cuenta en la misma moneda',
            slug='cmm',
            titular=titular,
            fecha_creacion=fecha,
            moneda=cuenta_cambiada.moneda,
        )
        cantidad_de_saldos_de_cuenta_en_la_misma_moneda = cuenta_en_la_misma_moneda.saldo_set.count()
        saldo_cuenta_en_la_misma_moneda = cuenta_en_la_misma_moneda.saldo_en_mov(mov_distintas_monedas)
        importe = getattr(mov_distintas_monedas, f"importe_cta_{sentido}")

        mov_distintas_monedas.moneda = otra_cuenta.moneda
        setattr(mov_distintas_monedas, f"cta_{sentido}", cuenta_en_la_misma_moneda)
        mov_distintas_monedas.save()

        with pytest.raises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=cuenta_cambiada, movimiento=mov_distintas_monedas)
        assert cuenta_en_la_misma_moneda.saldo_set.count() == cantidad_de_saldos_de_cuenta_en_la_misma_moneda + 1
        assert \
            cuenta_en_la_misma_moneda.saldo_en_mov(mov_distintas_monedas) == saldo_cuenta_en_la_misma_moneda + importe

    @pytest.mark.parametrize("sentido", ["entrada", "salida"])
    def test_si_cambia_moneda_e_importe_impacta_en_saldo_de_ambas_cuentas_segun_cotizacion(
            self, sentido, euro, request):
        """ Si en un movimiento entre cuentas en distinta moneda cambia la moneda y el importe (no automáticamente),
            se reemplaza en el cálculo del saldo el importe anterior por el nuevo en el caso de la cuenta en la
            nueva moneda del movimiento y por el nuevo cotizado en el caso de la cuenta en la otra moneda
        """
        mov_distintas_monedas = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
        sentido_otra_cuenta = el_que_no_es(sentido, "entrada", "salida")

        cuenta = getattr(mov_distintas_monedas, f"cta_{sentido}")
        otra_cuenta = getattr(mov_distintas_monedas, f"cta_{sentido_otra_cuenta}")
        saldo = cuenta.saldo_en_mov(mov_distintas_monedas)
        saldo_otra_cuenta = otra_cuenta.saldo_en_mov(mov_distintas_monedas)
        importe_cuenta = getattr(mov_distintas_monedas, f"importe_cta_{sentido}")
        importe_otra_cuenta = getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")
        cotizacion = mov_distintas_monedas.cotizacion

        mov_distintas_monedas.moneda = otra_cuenta.moneda
        mov_distintas_monedas.importe = 5
        mov_distintas_monedas.save()

        assert round(mov_distintas_monedas.cotizacion, 2) == round(1 / cotizacion, 2)
        assert \
            abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")) == \
            mov_distintas_monedas.importe
        assert \
            abs(getattr(mov_distintas_monedas, f"importe_cta_{sentido}")) == \
            round(mov_distintas_monedas.importe / mov_distintas_monedas.cotizacion, 2)
        assert \
            cuenta.saldo_en_mov(mov_distintas_monedas) == \
            saldo - importe_cuenta + getattr(mov_distintas_monedas, f"importe_cta_{sentido}")
        assert \
            otra_cuenta.saldo_en_mov(mov_distintas_monedas) == \
            saldo_otra_cuenta - importe_otra_cuenta + \
            getattr(mov_distintas_monedas, f"importe_cta_{sentido_otra_cuenta}")
