from unittest.mock import call

import pytest

from diario.models import Cuenta, CuentaInteractiva, Moneda, Movimiento, SaldoDiario
from utils import errors


@pytest.fixture
def mock_calcular(mocker):
    return mocker.patch('diario.models.movimiento.SaldoDiario.calcular')


@pytest.fixture(autouse=True)
def dia(dia):
    return dia


def test_no_admite_cuentas_acumulativas(cuenta_acumulativa):
    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=errors.CUENTA_ACUMULATIVA_EN_MOVIMIENTO):
        Movimiento.crear(
            'movimiento sobre acum', 100, cta_entrada=cuenta_acumulativa)


def test_guarda_fecha_de_ultimo_dia_por_defecto(cuenta, dia_posterior):
    mov = Movimiento.crear(
        concepto='Cobranza en efectivo',
        importe=100,
        cta_entrada=cuenta
    )
    assert mov.fecha == dia_posterior.fecha


def test_mov_entrada_con_importe_negativo_se_crea_como_mov_salida(cuenta):
    mov = Movimiento.crear('Pago', -100, cta_entrada=cuenta)
    assert mov.cta_entrada is None
    assert mov.cta_salida == cuenta


def test_mov_salida_con_importe_negativo_se_crea_como_mov_entrada(cuenta):
    mov = Movimiento.crear('Pago', -100, cta_salida=cuenta)
    assert mov.cta_salida is None
    assert mov.cta_entrada == cuenta


def test_mov_traspaso_con_importe_negativo_intercambia_cta_entrada_y_salida(cuenta, cuenta_2):
    mov = Movimiento.crear(
        'Pago', -100, cta_entrada=cuenta_2, cta_salida=cuenta)
    assert mov.cta_salida == cuenta_2
    assert mov.cta_entrada == cuenta


def test_mov_con_importe_negativo_se_crea_con_importe_positivo(cuenta):
    mov = Movimiento.crear('Pago', -100, cta_entrada=cuenta)
    assert mov.importe == 100


def test_importe_cero_tira_error(cuenta):
    with pytest.raises(
            errors.ErrorImporteCero,
            match="Se intentó crear un movimiento con importe cero"
    ):
        Movimiento.crear('Pago', 0, cta_salida=cuenta)


def test_movimiento_se_guarda_como_no_automatico_por_defecto(cuenta):
    mov = Movimiento.crear('Pago', '200', cta_entrada=cuenta)
    assert not mov.es_automatico


def test_suma_importe_a_cta_entrada(cuenta, entrada):
    assert cuenta.saldo_en_mov(entrada) == entrada.importe
    assert cuenta.saldo() == entrada.importe


def test_resta_importe_de_cta_salida(cuenta, salida):
    assert cuenta.saldo() == -salida.importe


def test_puede_traspasar_saldo_de_una_cuenta_a_otra(cuenta, cuenta_2):
    saldo_cuenta = cuenta.saldo()
    saldo_cuenta_2 = cuenta_2.saldo()

    mov = Movimiento.crear(
        concepto='Depósito',
        importe=60,
        cta_entrada=cuenta_2,
        cta_salida=cuenta
    )

    assert cuenta.saldo() == saldo_cuenta - mov.importe
    assert cuenta_2.saldo() == saldo_cuenta_2 + mov.importe


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_llama_a_calcular_saldo_con_arg_correspondiente(mock_calcular, cuenta, sentido):
    mov = Movimiento.crear("Nuevo mov", 20, **{f"cta_{sentido}": cuenta})
    mock_calcular.assert_called_once_with(mov, sentido)


def test_mov_traspaso_llama_a_calcular_saldo_diario_con_salida_False_para_cta_entrada_y_salida_True_para_cta_salida(
        mock_calcular, cuenta, cuenta_2):
    mov = Movimiento.crear("Traspaso", 20, cuenta, cuenta_2)
    assert mock_calcular.call_args_list == [call(mov, "entrada"), call(mov, "salida")]


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_integrativo_calcula_saldo_diario_si_no_existe(cuenta, dia, sentido):
    with pytest.raises(SaldoDiario.DoesNotExist):
        SaldoDiario.tomar(cuenta=cuenta, dia=dia)
    mov = Movimiento.crear("Nuevo mov", 20, dia=dia, **{f"cta_{sentido}": cuenta})

    try:
        saldo = SaldoDiario.objects.get(cuenta=cuenta, dia=mov.dia)
    except SaldoDiario.DoesNotExist:
        raise AssertionError("No se calculó saldo diario")

    assert saldo.cuenta.pk == cuenta.pk
    assert saldo.dia == mov.dia


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_importe_de_saldo_diario_generado_es_igual_a_importe_de_saldo_diario_anterior_mas_importe_del_movimiento(
        cuenta, dia, sentido, entrada_anterior):
    importe_sda = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_anterior.dia).importe

    mov = Movimiento.crear("Nuevo mov único en el día", 20, dia=dia, **{f"cta_{sentido}": cuenta})

    saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)

    assert saldo_diario.importe == importe_sda + mov.importe_cta(sentido)


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_importe_de_saldo_diario_existente_es_igual_a_importe_de_saldo_diario_anterior_mas_suma_de_los_movimientos_del_dia(
        cuenta, dia, sentido, entrada_anterior, traspaso):
    importe_sda = SaldoDiario.tomar(cuenta=cuenta, dia=entrada_anterior.dia).importe

    mov = Movimiento.crear("Nuevo mov único en el día", 20, dia=dia, **{f"cta_{sentido}": cuenta})
    movs_dia_cuenta = cuenta.movs().filter(dia=dia)
    importe_mdc = 0
    for mov in movs_dia_cuenta:
        if cuenta == mov.cta_entrada:
            importe_mdc += mov.importe
        elif cuenta == mov.cta_salida:
            importe_mdc -= mov.importe
        else:
            raise ValueError("cuenta no interviene en movimiento")

    saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)

    assert saldo_diario.importe == importe_sda + importe_mdc


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_integrativo_modifica_saldo_diario_si_ya_existe(saldo_diario, sentido):
    importe_saldo_diario = saldo_diario.importe
    cuenta = saldo_diario.cuenta
    dia = saldo_diario.dia

    mov = Movimiento.crear("Nuevo mov", 20, dia=dia, **{f"cta_{sentido}": cuenta})
    saldo_diario.refresh_from_db()

    assert saldo_diario.importe == importe_saldo_diario + mov.importe_cta(sentido)


def test_integrativo_crear_movimiento_en_fecha_antigua_modifica_saldos_diarios_posteriores(
        cuenta, entrada, dia_anterior):
    importe_saldo = SaldoDiario.tomar(cuenta=cuenta, dia=entrada.dia).importe
    mov_anterior = Movimiento.crear("Movimiento anterior", 30, cuenta, dia=dia_anterior)
    assert SaldoDiario.tomar(cuenta=cuenta, dia=entrada.dia).importe == importe_saldo + mov_anterior.importe


@pytest.mark.parametrize('cta_entrada, cta_salida, moneda, cot', [
    ('cuenta_con_saldo_en_euros', 'cuenta_con_saldo_en_dolares', 'dolar', 1.2),
    ('cuenta_con_saldo_en_euros', 'cuenta_con_saldo_en_dolares', 'euro', 0.8),
    ('cuenta_con_saldo_en_dolares', 'cuenta_con_saldo_en_euros', 'dolar', 1.2),
    ('cuenta_con_saldo_en_dolares', 'cuenta_con_saldo_en_euros', 'euro', 0.8),
])
def test_impacta_en_saldo_de_cada_cuenta_segun_la_cotizacion_y_moneda_del_movimiento(
        cta_entrada, cta_salida, moneda, cot, fecha, request):
    ce: CuentaInteractiva = request.getfixturevalue(cta_entrada)
    cs: CuentaInteractiva = request.getfixturevalue(cta_salida)
    mon_mov: Moneda = request.getfixturevalue(moneda)
    cta_en_mon_mov = ce if ce.moneda == mon_mov else cs
    saldo_ce: float = ce.saldo()
    saldo_cs: float = cs.saldo()

    mov = Movimiento.crear(
        concepto='Movimiento entre cuentas con distinta moneda',
        cta_entrada=ce,
        cta_salida=cs,
        importe=10,
        fecha=fecha,
        moneda=mon_mov,
        cotizacion=cot,
    )

    ce.refresh_from_db()
    cs.refresh_from_db()

    assert ce.saldo() == round(saldo_ce + (10 * (1 if ce == cta_en_mon_mov else mov.cotizacion)), 2)
    assert cs.saldo() == round(saldo_cs - (10 * (1 if cs == cta_en_mon_mov else mov.cotizacion)), 2)


class TestMovimientoEntreCuentasDeDistintosTitulares:
    def test_genera_contramovimiento(self, cuenta, cuenta_ajena):
        cantidad = Movimiento.cantidad()
        mov = Movimiento.crear('Crédito', 100, cuenta, cuenta_ajena)
        assert Movimiento.cantidad() == cantidad + 2
        assert Movimiento.primere().concepto == 'Constitución de crédito'
        assert Movimiento.primere().importe == mov.importe

    def test_guarda_id_de_contramovimiento_en_movimiento(self, cuenta, cuenta_ajena):
        mov = Movimiento.crear('Credito', 100, cuenta, cuenta_ajena)
        contramov = Movimiento.tomar(concepto='Constitución de crédito')
        assert mov.id_contramov == contramov.id

    def test_contramovimiento_generado_se_marca_como_automatico(self, credito):
        contramov = Movimiento.tomar(id=credito.id_contramov)
        assert contramov.es_automatico

    @pytest.mark.parametrize('imp, fixt_ce, fixt_cs, concepto', [
        (10, 'cuenta', 'cuenta_ajena', 'Aumento de crédito'),
        (128, 'cuenta_ajena', 'cuenta', 'Cancelación de crédito'),
        (80, 'cuenta_ajena', 'cuenta', 'Pago a cuenta de crédito'),
        (150, 'cuenta_ajena', 'cuenta', 'Pago en exceso de crédito'),
    ])
    def test_genera_concepto_de_contramovimiento_segun_situacion_de_credito_existente(
            self, credito, imp, fixt_ce, fixt_cs, concepto, request):
        ce = request.getfixturevalue(fixt_ce)
        cs = request.getfixturevalue(fixt_cs)
        mov = Movimiento.crear('Entre titulares', imp, ce, cs)
        assert Movimiento.tomar(id=mov.id_contramov).concepto == concepto

    def test_si_cuenta_acreedora_tiene_saldo_cero_concepto_contramovimiento_es_constitucion_de_credito(
            self, credito):
        Movimiento.crear('Devolución', credito.importe, credito.cta_salida, credito.cta_entrada)
        mov = Movimiento.crear('Nuevo crédito', 100, credito.cta_entrada, credito.cta_salida)
        assert Movimiento.tomar(id=mov.id_contramov).concepto == 'Constitución de crédito'

    def test_genera_cuentas_credito_si_no_existen(self, cuenta, cuenta_ajena):
        cant_cuentas = Cuenta.cantidad()
        with pytest.raises(Cuenta.DoesNotExist):
            Cuenta.tomar(sk='_titular-otro')
        with pytest.raises(Cuenta.DoesNotExist):
            Cuenta.tomar(sk='_otro-titular')
        Movimiento.crear('Credito', 100, cuenta, cuenta_ajena)
        assert Cuenta.cantidad() == cant_cuentas + 2
        Cuenta.tomar(sk='_titular-otro')  # doesn't raise
        Cuenta.tomar(sk='_otro-titular')  # doesn't raise

    def test_asigna_a_cuentas_generadas_fecha_del_movimiento_como_fecha_de_creacion(
            self, cuenta, cuenta_ajena, fecha):
        Movimiento.crear('Credito', 100, cuenta, cuenta_ajena, fecha=fecha)
        assert Cuenta.tomar(sk='_titular-otro').fecha_creacion == fecha
        assert Cuenta.tomar(sk='_otro-titular').fecha_creacion == fecha

    def test_no_genera_cuentas_credito_si_ya_existen(self, credito):
        cant_cuentas = Cuenta.cantidad()
        Movimiento.crear('Crédito', 100, credito.cta_entrada, credito.cta_salida)
        assert Cuenta.cantidad() == cant_cuentas

    def test_si_ya_existe_un_credito_de_sentido_inverso_resta_importe_de_saldo_de_cuenta_credito(
            self, credito, cuenta_2, cuenta_ajena_2):
        importe = Movimiento.tomar(id=credito.id_contramov).cta_entrada.saldo()
        Movimiento.crear('Devolución', 60, cuenta_ajena_2, cuenta_2)
        assert Movimiento.tomar(id=credito.id_contramov).cta_entrada.saldo() == importe - 60

    def test_si_ya_existe_un_credito_de_sentido_inverso_suma_importe_a_saldo_de_cuenta_deuda(
            self, credito, cuenta_2, cuenta_ajena_2):
        importe = Movimiento.tomar(id=credito.id_contramov).cta_salida.saldo()
        Movimiento.crear('Devolución', 60, cuenta_ajena_2, cuenta_2)
        assert Movimiento.tomar(id=credito.id_contramov).cta_salida.saldo() == importe + 60

    def test_si_receptor_no_es_acreedor_de_emisor_agrega_receptor_como_deudor_de_emisor(
            self, credito):
        assert credito.cta_entrada.titular in credito.cta_salida.titular.deudores.all()

    def test_si_receptor_es_acreedor_de_emisor_no_agrega_receptor_como_deudor_de_emisor(
            self, credito):
        mov = Movimiento.crear('Devolución', 60, credito.cta_salida, credito.cta_entrada)
        assert mov.cta_entrada.titular not in credito.cta_salida.titular.deudores.all()

    def test_si_se_devuelve_el_total_de_lo_adeudado_se_cancela_deuda_entre_emisor_y_receptor(
            self, credito, mocker):
        mock_cancelar_deuda_de = mocker.patch(
            'diario.models.Titular.cancelar_deuda_de',
            autospec=True
        )
        Movimiento.crear(
            'Devolución total', credito.importe,
            credito.cta_salida, credito.cta_entrada
        )
        mock_cancelar_deuda_de.assert_called_once_with(
            credito.cta_salida.titular,
            credito.cta_entrada.titular
        )

    def test_si_se_devuelve_el_total_de_lo_adeudado_no_se_modifica_el_nombre_de_las_cuentas_credito(
            self, credito):
        nombre_cd = credito.cta_entrada.titular.cuenta_credito_con(credito.cta_salida.titular).nombre
        nombre_ca = credito.cta_salida.titular.cuenta_credito_con(credito.cta_entrada.titular).nombre

        Movimiento.crear(
            'Devolución total', credito.importe,
            credito.cta_salida, credito.cta_entrada
        )

        assert credito.cta_entrada.titular.cuenta_credito_con(credito.cta_salida.titular).nombre == nombre_cd
        assert credito.cta_salida.titular.cuenta_credito_con(credito.cta_entrada.titular).nombre == nombre_ca

    def test_si_no_se_devuelve_el_total_de_lo_adeudado_no_se_cancela_deuda(self, credito, mocker):
        mock_cancelar_deuda_de = mocker.patch('diario.models.Titular.cancelar_deuda_de')
        Movimiento.crear(
            'Devolución parcial', credito.importe - 1,
            credito.cta_salida, credito.cta_entrada
        )
        mock_cancelar_deuda_de.assert_not_called()

    def test_si_se_devuelve_mas_de_lo_adeudado_se_invierte_relacion_crediticia(self, credito):
        Movimiento.crear(
            'Devolución excesiva', credito.importe + 1,
            credito.cta_salida, credito.cta_entrada
        )
        assert credito.cta_entrada.titular not in credito.cta_salida.titular.deudores.all()
        assert credito.cta_salida.titular in credito.cta_entrada.titular.deudores.all()

    def test_si_se_devuelve_mas_de_lo_adeudado_cambia_nombre_de_cuentas_credito(self, credito):
        cuenta_deudora = credito.cta_entrada.titular.cuenta_credito_con(credito.cta_salida.titular)
        cuenta_acreedora = credito.cta_salida.titular.cuenta_credito_con(credito.cta_entrada.titular)
        Movimiento.crear(
            'Devolución excesiva', credito.importe + 1,
            credito.cta_salida, credito.cta_entrada
        )
        cuenta_deudora.refresh_from_db()
        cuenta_acreedora.refresh_from_db()
        assert \
            cuenta_deudora.nombre == \
            f'Préstamo de {cuenta_deudora.titular.nombre} a {cuenta_acreedora.titular.nombre}'.lower()
        assert \
            cuenta_acreedora.nombre == \
            f'Deuda de {cuenta_acreedora.titular.nombre} con {cuenta_deudora.titular.nombre}'.lower()

    def test_si_se_presta_con_cuentas_credito_existentes_con_saldo_cero_y_nombres_opuestos_al_movimiento_cambia_nombre_de_cuentas_credito(
            self, credito):
        cuenta_deudora = credito.cta_entrada.titular.cuenta_credito_con(credito.cta_salida.titular)
        cuenta_acreedora = credito.cta_salida.titular.cuenta_credito_con(credito.cta_entrada.titular)
        Movimiento.crear("Devolución exacta", credito.importe, credito.cta_salida, credito.cta_entrada)
        Movimiento.crear("Préstamo en sentido opuesto al anterior", 100, credito.cta_salida, credito.cta_entrada)
        cuenta_deudora.refresh_from_db()
        cuenta_acreedora.refresh_from_db()

        assert \
            cuenta_deudora.nombre == \
            f'Préstamo de {cuenta_deudora.titular.nombre} a {cuenta_acreedora.titular.nombre}'.lower()
        assert \
            cuenta_acreedora.nombre == \
            f'Deuda de {cuenta_acreedora.titular.nombre} con {cuenta_deudora.titular.nombre}'.lower()

    def test_si_es_un_pago_a_cuenta_no_modifica_relacion_crediticia(self, credito):
        deudores_tit1 = list(credito.cta_entrada.titular.deudores.all())
        deudores_tit2 = list(credito.cta_salida.titular.deudores.all())
        Movimiento.crear(
            'Pago a cuenta', credito.importe - 1,
            credito.cta_salida, credito.cta_entrada
        )
        assert list(credito.cta_entrada.titular.deudores.all()) == deudores_tit1
        assert list(credito.cta_salida.titular.deudores.all()) == deudores_tit2
