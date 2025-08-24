from unittest.mock import ANY

import pytest
from django.core.exceptions import EmptyResultSet
from django.urls import reverse
from pytest_django import asserts

from diario.forms import FormCotizacion
from diario.models import Cotizacion


def test_get_usa_template_cotizacion_form(client, dolar):
    response = client.get(reverse('mon_cot_nueva', args=[dolar.sk]))
    asserts.assertTemplateUsed(response, 'diario/cotizacion_form.html')


def test_incluye_moneda_en_el_context(client, dolar):
    response = client.get(reverse('mon_cot_nueva', args=[dolar.sk]))
    assert response.context.get("moneda") == dolar


def test_usa_form_formcotizacion(client, dolar):
    response = client.get(reverse('mon_cot_nueva', args=[dolar.sk]))
    assert response.context.get('form') is not None
    assert isinstance(response.context['form'], FormCotizacion)


def test_crea_cotizacion_con_moneda_del_argumento_y_fecha_ingresada(client, dolar, fecha_inicial):
    with pytest.raises(EmptyResultSet):
        Cotizacion.tomar(moneda=dolar, fecha=fecha_inicial)

    client.post(
        reverse('mon_cot_nueva', args=[dolar.sk]),
        data={'fecha': fecha_inicial, 'importe_compra': 105, 'importe_venta': 108}
    )
    try:
        Cotizacion.tomar(moneda=dolar, fecha=fecha_inicial)
    except EmptyResultSet:
        raise AssertionError(f"No se creó cotización de moneda {dolar} en fecha {fecha_inicial}")


def test_post_redirige_a_home(client, dolar, fecha):
    response = client.post(
        reverse('mon_cot_nueva', args=[dolar.sk]),
        data={'fecha': fecha, 'importe_compra': 105, 'importe_venta': 108}
    )
    asserts.assertRedirects(response, reverse('home'))
