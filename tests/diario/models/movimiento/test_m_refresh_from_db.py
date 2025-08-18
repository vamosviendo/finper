from diario.models import CuentaInteractiva, CuentaAcumulativa
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_mantiene_tipos_especificos_de_cuentas_de_entrada_y_salida(cuenta, traspaso):
    dividir_en_dos_subcuentas(cuenta)
    traspaso.refresh_from_db()
    assert type(traspaso.cta_salida) == CuentaInteractiva
    assert type(traspaso.cta_entrada) == CuentaAcumulativa
