from __future__ import annotations

from datetime import date
from typing import cast, List, Type
from urllib.parse import urlparse

from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from diario.models import Cuenta, CuentaInteractiva, CuentaAcumulativa, Dia, Movimiento, Titular
from utils.numeros import float_format
from utils.tiempo import dia_de_la_semana
from vvmodel.models import MiModel
from vvsteps.driver import MiFirefox, MiWebElement


class FinperWebElement(MiWebElement):
    def texto_en_hijo(self, classname: str):
        """ Devuelve un str con el contenido de texto del elemento hijo
        que coincide con una clase css dada.
        """
        return self.encontrar_elemento(classname, By.CLASS_NAME).text


class FinperFirefox(MiFirefox):
    _web_element_cls = FinperWebElement

    # TODO: Corregir en MiFirefox
    def completar_form(self, boton="id_btn_submit", **kwargs: str | int | float | bool | date):
        for key, value in kwargs.items():
            self.completar(f"id_{key}", value)
        self.pulsar(boton)

    # TODO: Corregir en MiFirefox
    def assert_url(self, url: str):
        parsed_url = urlparse(self.current_url)
        url_real = parsed_url.path
        if len(parsed_url.query) > 0:
            url_real += f"?{parsed_url.query}"
        assert url == url_real, f"Url real '{url_real}' no coincide con url propuesta '{url}'"

    def cuenta_esta(self, cuenta: Cuenta) -> bool:
        nombres_cuenta = [x.text.strip() for x in self.encontrar_elementos('class_link_cuenta', fail=False)]
        return cuenta.nombre in nombres_cuenta

    def cliquear_en_cuenta(self, cuenta):
        self.encontrar_elemento(cuenta.nombre, By.LINK_TEXT).click()

    def cliquear_en_moneda(self, moneda):
        self.encontrar_elemento(moneda.nombre, By.LINK_TEXT).click()

    def cliquear_en_titular(self, titular):
        self.encontrar_elemento(titular.nombre, By.LINK_TEXT).click()

    def encontrar_movimiento(self, columna: str, contenido: str) -> MiWebElement:
        try:
            return self.encontrar_movimientos(columna, contenido)[0]
        except IndexError:
            raise NoSuchElementException(
                f'Contenido "{contenido}" no encontrado en columna "{columna}"'
            )

    def dict_movimiento(
            self,
            concepto: str,
            ocurrencia: int = 0
    ) -> dict[str, str]:
        titulos = self.encontrar_elemento("class_thead_movimientos", By.CLASS_NAME)
        movimiento = self.encontrar_movimientos("concepto", concepto)[ocurrencia]
        return dict(zip(textos_hijos(titulos, "th"), textos_hijos(movimiento, "td")))

    def encontrar_movimientos(self, columna: str, contenido: str) -> list[MiWebElement]:
        return [
            x for x in self.encontrar_elementos("class_row_mov", By.CLASS_NAME, fail=False)
            if x.encontrar_elemento(f"class_td_{columna}", By.CLASS_NAME).text == contenido
        ]

    def encontrar_dia(self, fecha: date) -> MiWebElement:
        return next(
            x for x in self.encontrar_elementos("class_div_dia")
            if x.encontrar_elemento("class_span_fecha_dia", By.CLASS_NAME).text ==
            f"{dia_de_la_semana[fecha.weekday()]} {fecha.strftime('%Y-%m-%d')}"
        )

    def encontrar_saldo_en_moneda_de_cuenta(self, sk: str) -> MiWebElement:
        return self\
            .encontrar_elemento(f'id_row_cta_{sk}')\
            .encontrar_elemento(f'.class_saldo_cuenta.mon_cuenta', By.CSS_SELECTOR)

    def encontrar_cotizacion(self, fecha: date) -> MiWebElement:
        cotizaciones = self.encontrar_elementos("class_row_cot")
        fecha_formateada = fecha.strftime("%Y-%m-%d")

        for cotizacion in cotizaciones:
            fecha_cot = cotizacion.encontrar_elemento("class_td_fecha", By.CLASS_NAME).text
            if fecha_cot == fecha_formateada:
                return cotizacion
        raise NoSuchElementException(f"No se encontró cotización con fecha {fecha_formateada}")

    def comparar_dias_de(self, ente: Cuenta | Titular) -> list[MiWebElement]:
        """ Dada una cuenta o un titular, comparar sus últimos 7 días con los que
            aparecen en la página.
            Si las comparaciones son correctas, devuelve lista de días de la página.
        """
        dias_db = ente.dias().reverse()[:7]
        dias_pag = self.encontrar_elementos("class_div_dia")

        assert dias_db.count() == len(dias_pag)
        for index, dia in enumerate(dias_pag):
            assert \
                cast(FinperWebElement, dia).texto_en_hijo("class_span_fecha_dia") == \
                dias_db[index].str_dia_semana()
            self.comparar_movimientos_de_dia_de(dia, dias_db[index], ente)
        return dias_pag

    def comparar_dia(self, dia_web: MiWebElement, dia_db: Dia):
        dia_web = cast(FinperWebElement, dia_web)
        assert dia_web.texto_en_hijo("class_span_fecha_dia") == dia_db.str_dia_semana()
        assert dia_web.texto_en_hijo("class_span_saldo_dia") == float_format(dia_db.saldo())
        self.comparar_movimientos_de_dia_de(dia_web, dia_db)

    def comparar_movimientos_de_dia_de(
            self,
            dia_web: MiWebElement,
            dia_db: Dia,
            ente: Cuenta | Titular | None = None):
        movs_dia_web = dia_web.encontrar_elementos("class_row_mov")
        movs_dia_db = dia_db.movs(ente)
        assert len(movs_dia_web) == movs_dia_db.count()

        for j, mov in enumerate(movs_dia_db):
            mov_web = cast(FinperWebElement, movs_dia_web[j])
            assert mov_web.texto_en_hijo("class_td_orden_dia") == str(mov.orden_dia)
            assert mov_web.texto_en_hijo("class_td_concepto") == mov.concepto
            assert mov_web.texto_en_hijo("class_td_detalle") == (
                (mov.detalle if len(mov.detalle) < 50 else f"{mov.detalle[:49]}…")
                if mov.detalle else ""
            )
            assert mov_web.texto_en_hijo("class_td_importe") == float_format(mov.importe)
            assert mov_web.texto_en_hijo("class_td_cta_entrada") == (mov.cta_entrada.nombre if mov.cta_entrada else "")
            assert mov_web.texto_en_hijo("class_td_cta_salida") == (mov.cta_salida.nombre if mov.cta_salida else "")

    def comparar_titular(self, titular: Titular):
        """ Dado un titular, comparar su nombre con el que encabeza la
            página. """
        nombre_titular = self.encontrar_elemento(
            'id_titulo_saldo_gral'
        ).text.strip()
        assert nombre_titular == f"Capital de {titular.nombre}:"

    def comparar_titulares_de(
            self, cuenta: CuentaInteractiva | CuentaAcumulativa):
        """ Dada una cuenta, comparar su titular o titulares con el o los
            que aparecen en la página. """
        nombres_titular = [cuenta.titular.nombre] if isinstance(cuenta, CuentaInteractiva) \
            else [x.nombre for x in cuenta.titulares]
        textos_titular = [
            x.text for x in self.encontrar_elementos(
                ".menu-item-content.class_div_nombre_titular",
                By.CSS_SELECTOR
            )
        ]
        assert nombres_titular == textos_titular

    def comparar_capital_de(self, titular: Titular):
        """ Dado un titular, comparar su capital con el que aparece en la
        página. """
        cap = self.encontrar_elemento('id_importe_saldo_gral').text.strip()
        assert cap == float_format(titular.capital())

    def comparar_capital_historico_de(self, titular: Titular, movimiento: Movimiento):
        """ Dado un titular y un movimiento, comparar el capital histórico del
            titular al momento del movimiento con el que aparece como saldo
            general de la página"""
        cap = self.encontrar_elemento('id_importe_saldo_gral').text.strip()
        assert cap == float_format(titular.capital(movimiento))

    def comparar_cuentas_de(self, titular: Titular):
        """ Dado un titular, comparar sus cuentas con las que aparecen en
            la página. """
        divs_cuenta = [
            x.text.strip()
            for x in self.encontrar_elementos('class_link_cuenta')
        ]
        nombres_cuenta = [
            x.nombre
            for x in titular.cuentas_interactivas().order_by('nombre')
        ]

        assert divs_cuenta == nombres_cuenta

    def comparar_cuenta(self, cuenta: Cuenta):
        """ Dada una cuenta, comparar su nombre con el que encabeza la página.
        """
        titulo = self.encontrar_elemento('id_div_saldo_gral').text.strip()
        assert titulo == \
               f"{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion}): " \
               f"{float_format(cuenta.saldo())}"

    def comparar_subcuentas_de(self, cuenta: CuentaAcumulativa):
        """ Dada una cuenta acumulativa, comparar sus subcuentas con las que
            aparecen en la página. """
        nombres_subcuenta = [
            x.text.strip() for x in self.encontrar_elementos('class_link_cuenta')]
        assert nombres_subcuenta == [
            x.nombre for x in cuenta.subcuentas.all()
        ]

    def comparar_saldo_de(self, cuenta: Cuenta):
        """ Dada una cuenta, comparar su saldo con el que aparece en la página.
        """
        saldo = self.encontrar_elemento('id_importe_saldo_gral').text.strip()
        assert saldo == float_format(cuenta.saldo())

    def comparar_saldo_historico_de(self, cuenta: Cuenta, movimiento: Movimiento):
        """ Dada una cuenta, comparar su saldo con el que aparece en la página.
        """
        saldo = self.encontrar_elemento('id_importe_saldo_gral').text.strip()
        assert saldo == float_format(cuenta.saldo(movimiento))

    # TODO: Pasar a MiFirefox
    def verificar_link(
            self,
            nombre: str,
            viewname: str,
            args: list | None = None,
            querydict: dict | None = None,
            criterio: str = By.ID,
    ):
        url_inicial = urlparse(self.current_url).path
        if criterio == By.CLASS_NAME:
            tipo = "class"
        else:
            tipo = "id"

        if querydict:
            querystring = "?"
            for key, value in querydict.items():
                querystring += f"{key}={value}&"
            querystring = querystring[:-1]  # Retiramos el último &. Ya sé que es desprolijo.
        else:
            querystring = ""

        self.encontrar_elemento(f"{tipo}_link_{nombre}", criterio).click()
        self.assert_url(reverse(viewname, args=args) + querystring)
        self.ir_a_pag(url_inicial)

    def crear_movimiento(self, **kwargs):
        self.ir_a_pag(reverse('mov_nuevo'))
        self.completar_form(**kwargs)


def texto_en_hijos_respectivos(
        classname: str,
        lista_elementos: List[MiWebElement]
) -> List[str]:
    """ A partir de una lista de elementos web, devuelve una lista de str
        con el contenido del hijo de cada uno de esos elementos de una
        clase css dada.
    """
    lista_elementos = cast(list[FinperWebElement], lista_elementos)
    return [x.texto_en_hijo(classname) for x in lista_elementos]


def textos_hijos(elemento: MiWebElement, tag_subelem: str) -> List[str]:
    return [x.text for x in elemento.encontrar_elementos(tag_subelem, By.TAG_NAME)]


def assert_exists(sk: str, cls: Type[MiModel]):
    try:
        cls.tomar(sk=sk)
    except cls.DoesNotExist:
        raise AssertionError(f"No existe {cls} con sk {sk}")
