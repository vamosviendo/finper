from datetime import date


def test_guarda_fecha_conversion(cuenta):
    fecha = date.today()
    cta_acum = cuenta.dividir_y_actualizar(
        ['subi1', 'si1', 0], ['subi2', 'si2']
    )
    assert cta_acum.fecha_conversion == fecha
