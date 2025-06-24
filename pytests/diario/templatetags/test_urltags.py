import pytest

from django.test import RequestFactory
from django.template import Context

from diario.templatetags.urltags import pageurl


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
