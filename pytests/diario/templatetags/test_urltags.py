import pytest

from django.test import RequestFactory
from django.template import Context
from django.urls import reverse

from diario.templatetags.urltags import movurl, pageurl


class TestMovUrl:
    def test_si_no_recibe_sk_de_titular_ni_de_cuenta_devuelve_url_de_movimiento(self, entrada):
        assert movurl(entrada) == reverse("movimiento", args=[entrada.pk])

    def test_si_recibe_sk_de_titular_devuelve_url_de_titular_y_movimiento(self, entrada, titular):
        assert movurl(entrada, tit_sk=titular.sk) == reverse("titular_movimiento", args=[titular.sk, entrada.pk])

    def test_si_recibe_sk_de_cuenta_devuelve_url_de_cuenta_y_movimiento(self, entrada, cuenta):
        assert movurl(entrada, cta_sk=cuenta.sk) == reverse("cuenta_movimiento", args=[cuenta.sk, entrada.pk])

    def test_si_recibe_sk_de_titular_y_de_cuenta_devuelve_url_de_cuenta_y_movimiento(self, entrada, titular, cuenta):
        assert movurl(entrada, tit_sk=titular.sk, cta_sk=cuenta.sk) == reverse("cuenta_movimiento", args=[cuenta.sk, entrada.pk])

    @pytest.mark.parametrize("argname, arg, viewname", [
        (None, None, "movimiento"),
        ("tit_sk", "titular", "titular_movimiento"),
        ("cta_sk", "c", "cuenta_movimiento")])
    def test_si_recibe_nro_de_pagina_agrega_querystring_con_pagina_al_url_devuelto(
            self, entrada, argname, arg, viewname):
        kwargs = dict()
        if argname and arg:
            kwargs = {argname: arg}
            base_url = reverse(viewname, args=[arg, entrada.pk])
        else:
            base_url = reverse(viewname, args=[entrada.pk])
        assert movurl(entrada, page=2, **kwargs) == base_url + "?page=2"

    @pytest.mark.parametrize("argname, arg, viewname", [
        (None, None, "movimiento"),
        ("tit_sk", "titular", "titular_movimiento"),
        ("cta_sk", "c", "cuenta_movimiento")])
    def test_si_recibe_fecha_agrega_querystring_con_fecha_al_url_devuelto(self, entrada, fecha, argname, arg, viewname):
        kwargs = dict()
        if argname and arg:
            kwargs = {argname: arg}
            base_url = reverse(viewname, args=[arg, entrada.pk])
        else:
            base_url = reverse(viewname, args=[entrada.pk])
        assert movurl(entrada, fecha=fecha, **kwargs) == base_url + f"?fecha={fecha}"

    def test_si_recibe_fecha_y_pagina_prioriza_fecha(self, entrada, fecha):
        assert \
            movurl(entrada, fecha=fecha, page=2) == \
            reverse("movimiento", args=[entrada.pk]) + f"?fecha={fecha}"


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
