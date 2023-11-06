from diario.models import Moneda


def test_guarda_y_recupera_monedas():
    moneda = Moneda()
    moneda.nombre = "Moneda"
    moneda.monname = "mn"
    moneda.cotizacion = 1.5
    moneda.full_clean()
    moneda.save()

    assert Moneda.cantidad() == 1
    mon = Moneda.tomar(monname="mn")
    assert mon.nombre == "Moneda"
    assert mon.cotizacion == 1.5
