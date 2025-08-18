import pytest

from diario.models import Cuenta, Titular


class TestMetodoCancelarDeudaDe:

    def test_retira_otro_titular_de_deudores_del_titular(self, titular, otro_titular, credito):
        otro_titular.cancelar_deuda_de(titular)
        assert titular not in otro_titular.deudores.all()

    def test_si_otro_no_esta_entre_deudores_del_titular_lanza_excepcion(self, titular, otro_titular):
        with pytest.raises(
                Titular.DoesNotExist,
                match=f'{titular.nombre} no figura '
                      f'entre los deudores de {otro_titular.nombre}'
        ):
            otro_titular.cancelar_deuda_de(titular)


class TestMetodoCuentaCreditoCon:
    def test_devuelve_cuenta_correspondiente_al_credito_con_otro_titular(
            self, titular, otro_titular, credito):
        assert \
            titular.cuenta_credito_con(otro_titular) == \
            Cuenta.tomar(sk=f'_{titular.sk}-{otro_titular.sk}')
        assert \
            otro_titular.cuenta_credito_con(titular) == \
            Cuenta.tomar(sk=f'_{otro_titular.sk}-{titular.sk}')

    def test_devuelve_none_si_no_hay_relacion_crediticia_con_otro_titular(
            self, titular, otro_titular):
        assert titular.cuenta_credito_con(otro_titular) is None
        assert otro_titular.cuenta_credito_con(titular) is None


class TestMetodoDeudaCon:
    def test_devuelve_importe_de_deuda_con_otro_titular(
            self, titular, otro_titular, credito):
        assert titular.deuda_con(otro_titular) == credito.importe

    def test_devuelve_0_si_no_hay_deuda(self, titular, otro_titular):
        assert titular.deuda_con(otro_titular) == 0

    def test_devuelve_0_si_el_titular_es_acreedor_del_otro(
            self, titular, otro_titular, credito):
        assert otro_titular.deuda_con(titular) == 0

    def test_devuelve_0_si_el_titular_es_deudor_de_otro_titular(
            self, titular, titular_gordo, credito):
        assert titular.deuda_con(titular_gordo) == 0


class TestMetodoEsDeudorDe:
    def test_devuelve_false_si_titular_no_esta_entre_deudores_de_otro(
            self, titular, otro_titular):
        assert titular.es_deudor_de(otro_titular) is False

    def test_devuelve_true_si_titular_esta_entre_deudores_de_otro(
            self, titular, otro_titular, credito):
        assert titular.es_deudor_de(otro_titular) is True


class TestMetodoEsAcreedorDe:
    def test_devuelve_false_si_titular_no_esta_entre_los_acreedores_de_otro(
            self, titular, otro_titular):
        assert otro_titular.es_acreedor_de(titular) is False

    def test_devuelve_true_si_titular_esta_entre_los_acreedores_de_otro(
            self, titular, otro_titular, credito):
        assert otro_titular.es_acreedor_de(titular) is True
