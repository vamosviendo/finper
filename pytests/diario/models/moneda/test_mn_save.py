from diario.models import Moneda, Cotizacion


def test_si_tiene_atributo__cotizacion_crea_cotizacion(mock_today):
    moneda = Moneda(nombre="moneda", monname="mn")
    moneda._cotizacion = Cotizacion(fecha=mock_today.return_value, importe=2.5)
    moneda.full_clean()
    moneda.save()

    assert Cotizacion.filtro(moneda=moneda, fecha=mock_today.return_value).exists()
    cotizacion = Cotizacion.tomar(moneda=moneda, fecha=mock_today.return_value)
    assert cotizacion.importe == 2.5


def test_si_no_tiene_atributo__cotizacion_no_crea_cotizacion(mock_today):
    moneda = Moneda(nombre="moneda", monname="mn")
    moneda.full_clean()
    moneda.save()

    assert not Cotizacion.filtro(moneda=moneda, fecha=mock_today.return_value).exists()


def test_si_tiene_atributo__cotizacion_y_ya_existe_cotizacion_con_esa_fecha_actualiza_importe(dolar, mock_today):
    Cotizacion.crear(moneda=dolar, fecha=mock_today.return_value, importe=2)
    dolar._cotizacion = Cotizacion(moneda=dolar, fecha=mock_today.return_value, importe=3)
    dolar.save()

    cotizacion = Cotizacion.tomar(moneda=dolar, fecha=mock_today.return_value)
    assert cotizacion.importe == 3
