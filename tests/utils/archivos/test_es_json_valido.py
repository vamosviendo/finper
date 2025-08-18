from utils.archivos import es_json_valido


def test_devuelve_true_si_el_archivo_es_json(archivo_json):
    assert es_json_valido(archivo_json) is True


def test_devuelve_false_si_el_archivo_no_es_json(archivo_vacio_ro):
    assert es_json_valido(archivo_vacio_ro) is False