from __future__ import annotations

from datetime import date
from typing import List
from urllib.parse import urlparse

from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from diario.models import Cuenta, CuentaInteractiva, CuentaAcumulativa, Dia, Movimiento, Titular
from utils.numeros import float_format
from utils.tiempo import dia_de_la_semana, str2date
from vvsteps.driver import MiFirefox, MiWebElement
from vvsteps.helpers import esperar


class FinperFirefox(MiFirefox):

    # TODO: ¿pasar a MiFirefox?
    def __init__(self, base_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = base_url

    # TODO: pasar a MiFirefox
    def ir_a_pag(self, url: str = ''):
        self.get(f"{self.base_url}{url}")

    # TODO: pasar a MiFirefox
    @esperar
    def assert_url(self, url: str):
        assert url == urlparse(self.current_url).path

    # TODO: pasar a MiFirefox o eliminar si no se la usa
    @esperar
    def esperar_que_no_este(self, elemento, criterio=By.ID):
        try:
            self.find_element(criterio, elemento)
            raise AssertionError(
                f'El elemento {elemento}, que no debería existir, existe'
            )
        except NoSuchElementException:
            pass

    # TODO: pasar a MiFirefox
    def completar_form(self, **kwargs: str | date):
        for key, value in kwargs.items():
            self.completar(f"id_{key}", value)
        self.pulsar()

    def cliquear_en_cuenta(self, cuenta):
        self.esperar_elemento(cuenta.nombre, By.LINK_TEXT).click()

    def cliquear_en_titular(self, titular):
        self.esperar_elemento(titular.nombre, By.LINK_TEXT).click()

    def esperar_movimiento(self, columna: str, contenido: str) -> MiWebElement:
        try:
            return self.esperar_movimientos(columna, contenido)[0]
        except IndexError:
            raise NoSuchElementException(
                f'Contenido "{contenido}" no encontrado en columna "{columna}"'
            )

    def esperar_movimientos(self, columna: str, contenido: str) -> list[MiWebElement]:
        return [
            x for x in self.esperar_elementos("class_row_mov", By.CLASS_NAME, fail=False)
            if x.esperar_elemento(f"class_td_{columna}", By.CLASS_NAME).text == contenido
        ]

    def esperar_dia(self, fecha: date) -> MiWebElement:
        return next(
            x for x in self.esperar_elementos("class_div_dia")
            if x.esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text ==
            f"{dia_de_la_semana[fecha.weekday()]} {fecha.strftime('%Y-%m-%d')}"
        )

    def esperar_saldo_en_moneda_de_cuenta(self, slug: str) -> MiWebElement:
        return self\
            .esperar_elemento(f'id_row_cta_{slug}')\
            .esperar_elemento(f'.class_saldo_cuenta.mon_cuenta', By.CSS_SELECTOR)

    def serializar_dias_pagina(self) -> list[dict[str, str | list[dict[str, MiWebElement | str]]]]:
        """ Devuelve una lista de diccionarios con datos de los días de la página.
            Cada diccionario de día incluye fecha y una lista de movimientos del día.
        """
        divs_dia = self.esperar_elementos("class_div_dia")
        result = list()
        for dia in divs_dia:
            result.append({
                'fecha': dia.esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text,
                'movimientos': [{
                    'webelement': mov,
                    'concepto': mov.esperar_elemento("class_td_concepto", By.CLASS_NAME).text,
                    'importe': mov.esperar_elemento("class_td_importe", By.CLASS_NAME).text,
                    'cta_entrada': mov.esperar_elemento("class_td_cta_entrada", By.CLASS_NAME).text,
                    'cta_salida': mov.esperar_elemento("class_td_cta_salida", By.CLASS_NAME).text,
                } for mov in dia.esperar_elementos("class_row_mov")]
            })
        return result

    def comparar_dias_de(self, ente: Cuenta | Titular) -> list[dict[str, str | list[dict[str, MiWebElement | str]]]]:
        """ Dada una cuenta o un titular, comparar sus últimos 7 días con los que
            aparecen en la página.
            Si las comparaciones son correctas, devuelve lista de días de la página serializados.
        """
        dias_db = ente.dias().reverse()[:7]
        dias_pag = self.serializar_dias_pagina()
        assert dias_db.count() == len(dias_pag)
        for index, dia in enumerate(dias_pag):
            assert dia["fecha"] == dias_db[index].str_dia_semana()
            self.comparar_movimientos_de_dia_de(ente, dia, dias_db[index])
        return dias_pag

    def comparar_movimientos_de_dia_de(
            self,
            ente: Cuenta | Titular,
            dia_pag: dict[str, str | list[dict[str, MiWebElement | str]]],
            dia_db: Dia):
        if isinstance(ente, Cuenta):
            movs_db = dia_db.movimientos_filtrados(cuenta=ente)
        elif isinstance(ente, Titular):
            movs_db = dia_db.movimientos_filtrados(titular=ente)
        else:
            movs_db = dia_db.movimientos_filtrados()
        for index, mov in enumerate(dia_pag["movimientos"]):
            assert mov["concepto"] == movs_db[index].concepto
            assert mov["importe"] == float_format(movs_db[index].importe)
            assert mov["cta_entrada"] == (movs_db[index].cta_entrada.nombre if movs_db[index].cta_entrada else "")
            assert mov["cta_salida"] == (movs_db[index].cta_salida.nombre if movs_db[index].cta_salida else "")

    def comparar_movimientos_de_fecha_de(self, ente: Cuenta | Titular, fecha: date, container: WebElement = None):
        """ Dado una ente que puede ser una cuenta o un titular,
            comparar sus movimientos con los que aparecen en
            la página en el día de la fecha dada. """
        container = container or self
        conceptos_mov = [
            x.text for x in container.esperar_elementos(
                '.class_row_mov td.class_td_concepto', By.CSS_SELECTOR
        )]
        assert conceptos_mov == [
            x.concepto for x in ente.movs() if x.fecha == fecha
        ]

    def comparar_titular(self, titular: Titular):
        """ Dado un titular, comparar su nombre con el que encabeza la
            página. """
        nombre_titular = self.esperar_elemento(
            'id_titulo_saldo_gral'
        ).text.strip()
        assert nombre_titular == f"Capital de {titular.nombre}:"

    def comparar_titulares_de(
            self, cuenta: CuentaInteractiva | CuentaAcumulativa):
        """ Dada una cuenta, comparar su titular o titulares con el o los
            que aparecen en la página. """
        nombres_titular = [cuenta.titular.nombre] if cuenta.es_interactiva \
            else [x.nombre for x in cuenta.titulares]
        textos_titular = [
            x.text for x in self.esperar_elementos(
                ".menu-item-content.class_div_nombre_titular",
                By.CSS_SELECTOR
            )
        ]
        assert nombres_titular == textos_titular

    def comparar_capital_de(self, titular: Titular):
        """ Dado un titular, comparar su capital con el que aparece en la
        página. """
        cap = self.esperar_elemento('id_importe_saldo_gral').text.strip()
        assert cap == float_format(titular.capital())

    def comparar_capital_historico_de(self, titular: Titular, movimiento: Movimiento):
        """ Dado un titular y un movimiento, comparar el capital histórico del
            titular al momento del movimiento con el que aparece como saldo
            general de la página"""
        cap = self.esperar_elemento('id_importe_saldo_gral').text.strip()
        assert cap == float_format(titular.capital(movimiento))

    def comparar_cuentas_de(self, titular: Titular):
        """ Dado un titular, comparar sus cuentas con las que aparecen en
            la página. """
        divs_cuenta = [
            x.text.strip()
            for x in self.esperar_elementos('class_link_cuenta')
        ]
        nombres_cuenta = [
            x.nombre
            for x in titular.cuentas_interactivas().order_by('nombre')
        ]

        assert divs_cuenta == nombres_cuenta

    def comparar_cuenta(self, cuenta: Cuenta):
        """ Dada una cuenta, comparar su nombre con el que encabeza la página.
        """
        titulo = self.esperar_elemento('id_div_saldo_gral').text.strip()
        assert titulo == \
               f"{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion}): " \
               f"{float_format(cuenta.saldo())}"

    def comparar_subcuentas_de(self, cuenta: CuentaAcumulativa):
        """ Dada una cuenta acumulativa, comparar sus subcuentas con las que
            aparecen en la página. """
        nombres_subcuenta = [
            x.text for x in self.esperar_elementos('class_link_cuenta')]
        assert nombres_subcuenta == [
            x.nombre for x in cuenta.subcuentas.all()
        ]

    def comparar_saldo_de(self, cuenta: Cuenta):
        """ Dada una cuenta, comparar su saldo con el que aparece en la página.
        """
        saldo = self.esperar_elemento('id_importe_saldo_gral').text.strip()
        assert saldo == float_format(cuenta.saldo())

    def comparar_saldo_historico_de(self, cuenta: Cuenta, movimiento: Movimiento):
        """ Dada una cuenta, comparar su saldo con el que aparece en la página.
        """
        saldo = self.esperar_elemento('id_importe_saldo_gral').text.strip()
        assert saldo == float_format(cuenta.saldo(movimiento))

    def verificar_link(
            self,
            nombre: str,
            viewname: str,
            args: list = None,
            criterio: str = By.ID,
            url_inicial: str = '',
    ):
        self.ir_a_pag(url_inicial)
        if criterio == By.CLASS_NAME:
            tipo = "class"
        else:
            tipo = "id"
        self.esperar_elemento(f"{tipo}_link_{nombre}", criterio).click()
        self.assert_url(reverse(viewname, args=args))

    def crear_movimiento(self, **kwargs):
        self.ir_a_pag(reverse('mov_nuevo'))
        self.completar_form(**kwargs)


def texto_en_hijos_respectivos(
        classname: str,
        lista_elementos: List[MiWebElement | WebElement]
) -> List[str]:
    """ A partir de una lista de elementos web, devuelve una lista de str
        con el contenido del hijo de cada uno de esos elementos de una
        clase css dada.
    """
    return [
        x.esperar_elemento(classname, By.CLASS_NAME).text
        for x in lista_elementos
    ]

