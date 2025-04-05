from diario.models import Moneda, Cotizacion


def test_si_tiene_atributo__cotizacion_crea_cotizacion(mock_today):
    moneda = Moneda(nombre="moneda", sk="mn")
    moneda._cotizacion = Cotizacion(fecha=mock_today.return_value, importe_compra=2.5, importe_venta=3)
    moneda.full_clean()
    moneda.save()

    assert Cotizacion.filtro(moneda=moneda, fecha=mock_today.return_value).exists()
    cotizacion = Cotizacion.tomar(moneda=moneda, fecha=mock_today.return_value)
    assert cotizacion.importe_compra == 2.5
    assert cotizacion.importe_venta == 3


def test_si_no_tiene_atributo__cotizacion_no_crea_cotizacion(mock_today):
    moneda = Moneda(nombre="moneda", sk="mn")
    moneda.full_clean()
    moneda.save()

    assert not Cotizacion.filtro(moneda=moneda, fecha=mock_today.return_value).exists()


def test_si_tiene_atributo__cotizacion_y_ya_existe_cotizacion_con_esa_fecha_actualiza_importe(dolar, mock_today):
    Cotizacion.crear(moneda=dolar, fecha=mock_today.return_value, importe_compra=2, importe_venta=2.5)
    dolar._cotizacion = Cotizacion(moneda=dolar, fecha=mock_today.return_value, importe_compra=2.8, importe_venta=3)
    dolar.save()

    cotizacion = Cotizacion.tomar(moneda=dolar, fecha=mock_today.return_value)
    assert cotizacion.importe_compra == 2.8
    assert cotizacion.importe_venta == 3
