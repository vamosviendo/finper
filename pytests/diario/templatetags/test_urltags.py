from __future__ import annotations

from datetime import date

import pytest
from django.db.models import QuerySet

from django.test import RequestFactory
from django.template import Context
from django.urls import reverse

from vvmodel.models import MiModel

from diario.models import Movimiento, Dia
from diario.templatetags.urltags import finperurl, movurl, pageurl, url_cuenta_nueva


def get_request_context(viewname: str, page: int | None = None, fecha: date | None = None, **kwargs) -> Context:
    objetos = [x for x in kwargs.values() if isinstance(x, MiModel)]
    claves = [x.pk if type(x) == Movimiento else x.sk for x in objetos]
    if page:
        querystring = f"?page={page}"
    elif fecha:
        querystring = f"?fecha={fecha}"
    else:
        querystring = ""
    factory = RequestFactory()
    request = factory.get(reverse(viewname, args=claves) + querystring)
    return Context({"request": request, **kwargs})


@pytest.fixture
def dias(dia: Dia, dia_anterior: Dia, dia_posterior: Dia) -> QuerySet[Dia]:
    return Dia.todes()


class TestFinperUrl:

    def test_si_recibe_titular_devuelve_url_de_detalle_de_titular(self, titular):
        context = get_request_context("titular", titular=titular)
        assert finperurl(context) == titular.get_absolute_url()

    def test_si_recibe_cuenta_devuelve_url_de_detalle_de_cuenta(self, cuenta):
        context = get_request_context("cuenta", cuenta=cuenta)
        assert finperurl(context) == cuenta.get_absolute_url()

    def test_si_recibe_movimiento_devuelve_url_de_detalle_de_movimiento(self, entrada, dias):
        context = get_request_context("movimiento", movimiento=entrada, dias=dias)
        assert finperurl(context) == entrada.get_absolute_url()

    def test_si_recibe_titular_y_movimiento_devuelve_url_de_detalle_de_titular_en_movimiento(
            self, titular, entrada, dias):
        context = get_request_context("titular_movimiento", titular=titular, movimiento=entrada, dias=dias)
        assert finperurl(context) == titular.get_url_with_mov(entrada)

    def test_si_recibe_cuenta_y_movimiento_devuelve_url_de_detalle_de_cuenta_en_movimiento(
            self, cuenta, entrada, dias):
        context = get_request_context("cuenta_movimiento", cuenta=cuenta, movimiento=entrada, dias=dias)
        assert finperurl(context) == cuenta.get_url_with_mov(entrada)

    def test_si_no_recibe_titular_cuenta_ni_movimiento_devuelve_url_home(self):
        context = get_request_context("home")
        assert finperurl(context) == reverse("home")

    def test_si_recibe_movimiento_no_incluido_en_los_dias_de_la_pagina_devuelve_url_sin_movimiento(
            self, cuenta, mas_de_7_dias):
        mov = Movimiento.crear(concepto="Movimiento", importe=100, dia=mas_de_7_dias[7], cta_entrada=cuenta)
        context = get_request_context("movimiento", movimiento=mov, dias=mas_de_7_dias[:6])
        assert finperurl(context) == reverse("home")

    def test_si_recibe_cuenta_y_movimiento_no_incluido_en_los_dias_de_la_pagina_devuelve_url_sin_movimiento(
            self, cuenta, mas_de_7_dias):
        mov = Movimiento.crear(concepto="Movimiento", importe=100, dia=mas_de_7_dias[7], cta_entrada=cuenta)
        context = get_request_context(
            "cuenta_movimiento", cuenta=cuenta, movimiento=mov, dias=mas_de_7_dias[:6]
        )
        assert finperurl(context) == cuenta.get_absolute_url()

    def test_si_recibe_titular_y_movimiento_no_incluido_en_los_dias_de_la_pagina_devuelve_url_sin_movimiento(
            self, titular, cuenta, mas_de_7_dias):
        mov = Movimiento.crear(concepto="Movimiento", importe=100, dia=mas_de_7_dias[7], cta_entrada=cuenta)
        context = get_request_context("titular_movimiento", titular=titular, movimiento=mov, dias=mas_de_7_dias[:6])
        assert finperurl(context) == titular.get_absolute_url()

    @pytest.mark.xfail
    def test_si_no_recibe_dias_da_valueerror(self):
        pytest.fail("escribir")

class TestMovUrl:
    def test_si_no_recibe_sk_de_titular_ni_de_cuenta_devuelve_url_de_movimiento(self, entrada):
        context = dict()
        assert movurl(context, entrada) == entrada.get_absolute_url()

    def test_si_recibe_sk_de_titular_devuelve_url_de_titular_y_movimiento(self, entrada, titular):
        context = {"titular": titular}
        assert movurl(context, entrada) == titular.get_url_with_mov(entrada)

    def test_si_recibe_sk_de_cuenta_devuelve_url_de_cuenta_y_movimiento(self, entrada, cuenta):
        context = {"cuenta": cuenta}
        assert movurl(context, entrada) == cuenta.get_url_with_mov(entrada)

    def test_si_recibe_sk_de_titular_y_de_cuenta_devuelve_url_de_cuenta_y_movimiento(self, entrada, titular, cuenta):
        context = {"titular": titular, "cuenta": cuenta}
        assert movurl(context, entrada) == cuenta.get_url_with_mov(entrada)

    @pytest.mark.parametrize("origen", [None, "titular", "cuenta"])
    def test_si_recibe_nro_de_pagina_agrega_querystring_con_pagina_al_url_devuelto(
            self, origen, entrada, request):
        if origen:
            ente = request.getfixturevalue(origen)
            context = {origen: ente}
            base_url = ente.get_url_with_mov(entrada)
        else:
            context = dict()
            base_url = entrada.get_absolute_url()
        assert movurl(context, entrada, page=2) == base_url + "?page=2"

    @pytest.mark.parametrize("origen", [None, "titular", "cuenta"])
    def test_si_recibe_fecha_agrega_querystring_con_fecha_al_url_devuelto(self, origen, entrada, fecha, request):
        if origen:
            ente = request.getfixturevalue(origen)
            context = {origen: ente}
            base_url = ente.get_url_with_mov(entrada)
        else:
            context = dict()
            base_url = entrada.get_absolute_url()
        assert movurl(context, entrada, fecha=fecha) == base_url + f"?fecha={fecha}"

    def test_si_recibe_fecha_y_pagina_prioriza_fecha(self, entrada, fecha):
        context = dict()
        assert \
            movurl(context, entrada, fecha=fecha, page=2) == entrada.get_absolute_url() + f"?fecha={fecha}"


class TestPageUrl:
    @pytest.mark.parametrize("url_actual", ["/", "/diario/c/c/", "/diario/t/titular/"])
    def test_devuelve_url_actual_con_querystring_indicando_pagina_y_marcador(self, url_actual):
        factory = RequestFactory()
        request = factory.get(url_actual)
        context = Context({"request": request})
        assert pageurl(context, 2) == f"{url_actual}?page=2#id_section_movimientos"

    @pytest.mark.parametrize("url_actual", ["/", "/diario/c/c/", "/diario/t/titular/"])
    def test_si_no_recibe_nro_de_pagina_devuelve_url_actual_con_marcador(self, url_actual):
        factory = RequestFactory()
        request = factory.get(url_actual)
        context = Context({"request": request})
        assert pageurl(context) == f"{url_actual}#id_section_movimientos"

    @pytest.mark.parametrize(
        "url_actual, path_devuelto", [
            ("/diario/m/256", "/"),
            ("/diario/cm/c/256", "/diario/c/c/"),
            ("/diario/tm/titular/256", "/diario/t/titular/")
        ]
    )
    def test_si_url_actual_incluye_movimiento_se_lo_elimina_de_la_url_devuelta(self, url_actual, path_devuelto):
        factory = RequestFactory()
        request = factory.get(url_actual)
        context = Context({"request": request})
        assert pageurl(context, 2) == f"{path_devuelto}?page=2#id_section_movimientos"

class TestUrlCuentaNueva:
    def test_si_no_hay_cuenta_en_el_context_devuelve_url_de_cuenta_nueva(self):
        context = dict()
        assert url_cuenta_nueva(context) == reverse("cta_nueva")

    def test_si_hay_cuenta_interactiva_en_el_context_devuelve_url_de_dividir_entre(
            self, cuenta):
        context = {"cuenta": cuenta}
        assert url_cuenta_nueva(context) == reverse("cta_div", args=[cuenta.sk])

    def test_si_hay_cuenta_acumulativa_en_el_context_devuelve_url_de_agregar_cuenta(
            self, cuenta_acumulativa):
        context = {"cuenta": cuenta_acumulativa}
        assert url_cuenta_nueva(context) == reverse("cta_agregar_subc", args=[cuenta_acumulativa.sk])
