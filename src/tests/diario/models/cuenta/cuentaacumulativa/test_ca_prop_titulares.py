from django.db import connection
from django.test.utils import CaptureQueriesContext


def test_devuelve_lista_de_titulares_de_subcuentas_sin_elementos_repetidos(cuenta_acumulativa, titular, otro_titular):
    cuenta_acumulativa.agregar_subcuenta('subcuenta 3', 'sc3', titular)
    sc1, sc2, sc3 = cuenta_acumulativa.subcuentas.all()
    sc1.titular = titular
    sc1.save()
    sc2.titular = otro_titular
    sc2.save()
    sc3.titular = titular
    sc3.save()

    assert cuenta_acumulativa.titulares == [titular, otro_titular]


def test_si_subcuenta_es_acumulativa_incluye_titulares_de_subcuenta(
        cuenta_acumulativa, titular, otro_titular, titular_gordo):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    sc2.titular = otro_titular
    sc2.save()

    sc1 = sc1.dividir_y_actualizar(
        ['subsubcuenta 1.1', 'ssc11', 50],
        ['subsubcuenta 1.2', 'ssc12']
    )
    ssc11, ssc12 = sc1.subcuentas.all()
    ssc11.titular = titular
    ssc11.save()
    ssc12.titular = titular_gordo
    ssc12.save()

    assert set(cuenta_acumulativa.titulares) == {titular, otro_titular, titular_gordo}


def test_no_genera_query_por_cada_subcuenta(
        cuenta_acumulativa, titular, otro_titular, cuenta_de_dos_titulares):
    # Pre-cargar para no contar queries de setup
    list(cuenta_acumulativa.titulares)

    with CaptureQueriesContext(connection) as ctx:
        titulares = cuenta_acumulativa.titulares

    # Debe traer todos los titulares en una sola query, no una por subcuenta
    assert titular in titulares
    queries = sum(1 for q in ctx.captured_queries if "diario_cuenta" in q["sql"])
    assert queries <= 1
