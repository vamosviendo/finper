from datetime import date
from unittest.mock import MagicMock

import pytest
from django.urls import reverse
from pytest_django import asserts

from diario.models import Dia, Cuenta, Titular, Movimiento


@pytest.fixture(autouse=True)
def titular_principal(mocker, titular: Titular) -> MagicMock:
    return mocker.patch('diario.forms.TITULAR_PRINCIPAL', titular.sk)


@pytest.fixture
def post_data_movimiento(dia: Dia, importe: float, cuenta: Cuenta) -> dict:
    return {
            'fecha': dia.fecha,
            'concepto': 'mov nuevo',
            'importe': importe,
            'cta_entrada': cuenta.pk,
            'moneda': cuenta.moneda.pk,
            'submit': '1',
        }


@pytest.fixture
def post_data_cuenta(fecha: date, titular: Titular) -> dict:
    return {
        'nombre': 'Cuenta nueva',
        'sk': 'c',
        'titular': titular.pk,
        'fecha_creacion': fecha
    }


@pytest.fixture
def post_data_titular(fecha: date) -> dict:
    return {'sk': 'tito', 'nombre': 'Tito Gómez', 'fecha_alta': fecha}


@pytest.mark.parametrize("viewname, fixt, post_data, tipo_origen, fixt_origen", [
    ("mov_nuevo", None, "post_data_movimiento", "c", "cuenta"),
    ("mov_mod", "entrada", "post_data_movimiento", "c", "cuenta"),
    ("mov_elim", "entrada", None, "c", "cuenta"),
    ("cta_nueva", None, "post_data_cuenta", "t", "titular"),
    ("cta_mod", "cuenta", "post_data_cuenta", "t", "titular"),
    ("cta_elim", "cuenta", "post_data_cuenta", "t", "titular"),
])
def test_post_redirige_a_url_recibida_en_querystring(
        client, tipo_origen, fixt_origen, viewname, fixt, post_data, request):

    objeto_origen = request.getfixturevalue(fixt_origen)
    data = request.getfixturevalue(post_data) if post_data else None
    origen = f"/diario/{tipo_origen}/{objeto_origen.sk}/"

    # TODO: Reemplazar después de corregir en urls.py modo de selección de movimientos
    #       Eliminar este párrafo y descomentar texto siguiente.
    if fixt:
        objeto = request.getfixturevalue(fixt)
        if isinstance(objeto, Movimiento):
            args = [objeto.pk]
        else:
            args = [objeto.sk]
    else:
        args = []

    # args = [request.getfixturevalue(fixt).sk] if fixt else []

    response = client.post(
        reverse(viewname, args=args) + f"?next={origen}",
        data=data,
    )

    asserts.assertRedirects(response, origen)


@pytest.mark.parametrize("viewname, fixt, post_data", [
    ("mov_nuevo", None, "post_data_movimiento"),
    ("mov_mod", "entrada", "post_data_movimiento"),
    ("mov_elim", "entrada", None),
    ("cta_nueva", None, "post_data_cuenta"),
    ("cta_mod", "cuenta", "post_data_cuenta"),
    ("cta_elim", "cuenta", "post_data_cuenta"),
])
def test_post_redirige_a_home_si_no_recibe_url_en_querystring(
    client, viewname, fixt, post_data, request):
    data = request.getfixturevalue(post_data) if post_data else None

    # TODO: Reemplazar después de corregir en urls.py modo de selección de movimientos
    #       Eliminar este párrafo y descomentar texto siguiente.
    if fixt:
        objeto = request.getfixturevalue(fixt)
        if isinstance(objeto, Movimiento):
            args = [objeto.pk]
        else:
            args = [objeto.sk]
    else:
        args = []

    response = client.post(
        reverse(viewname, args=args),
        data=data,
    )

    asserts.assertRedirects(response, reverse("home"))
