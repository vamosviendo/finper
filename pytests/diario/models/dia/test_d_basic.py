from diario.models import Dia


def test_guarda_y_recupera_dias(fecha):
    dia = Dia()
    dia.fecha = fecha
    dia.full_clean()
    dia.save()

    assert Dia.cantidad() == 1
    dia = Dia.tomar(fecha=fecha)     # No da error
