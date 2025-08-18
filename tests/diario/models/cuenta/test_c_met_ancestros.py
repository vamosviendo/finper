import pytest

from diario.models import CuentaInteractiva


def test_devuelve_lista_de_todas_las_cuentas_ancestro(cuenta: CuentaInteractiva):
    subc1, subc2 = cuenta.dividir_entre(
        ['subcuenta 1', 'sc1', 0],
        ['subcuenta 2', 'sc2']
    )
    subsubc1, subsubc2 = subc1.dividir_entre(
        ['subsubcuenta 1', 'ssc1', 0],
        ['subsubcuenta 2', 'ssc2']
    )
    subsubsubc1, subsubsubc2 = subsubc1.dividir_entre(
        ['subsubsubcuenta 1', 'sssc1', 0],
        ['subsubsubcuenta 2', 'sssc2']
    )
    subsubc1 = subsubc1.tomar_del_sk()
    subc1 = subc1.tomar_del_sk()
    cta = cuenta.tomar_del_sk()

    assert subsubsubc1.ancestros() == [subsubc1, subc1, cta]
