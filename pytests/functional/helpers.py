from __future__ import annotations

from typing import List
from urllib.parse import urlparse

from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from diario.models import Titular, Cuenta
from utils.numeros import float_format
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
    def completar_form(self, **kwargs: str):
        for key, value in kwargs.items():
            self.completar(f"id_{key}", value)
        self.pulsar()

    def cliquear_en_cuenta(self, cuenta):
        self.esperar_elemento(cuenta.nombre, By.LINK_TEXT).click()

    def cliquear_en_titular(self, titular):
        self.esperar_elemento(titular.nombre, By.LINK_TEXT).click()

    def esperar_movimiento(self, columna: str, contenido: str) -> MiWebElement:
        movimientos = self.esperar_elementos('class_row_mov', By.CLASS_NAME)
        try:
            return next(
                x for x in movimientos
                if x.find_element_by_class_name(f'class_td_{columna}').text
                    == contenido
            )
        except StopIteration:
            raise NoSuchElementException(
                f'Contenido {contenido} no encontrado en columna {columna}'
            )

    def comparar_movimientos_de(self, ente: Cuenta | Titular):
        """ Dada una cuenta, comparar sus movimientos con los que aparecen en
            la página. """
        conceptos_mov = [
            x.text for x in self.esperar_elementos(
                '.class_row_mov td.class_td_concepto', By.CSS_SELECTOR
        )]
        assert conceptos_mov == list(
            reversed(
                [x.concepto for x in ente.movs()]
            )
        )

    def comparar_titular(self, titular: Titular):
        """ Dado un titular, comparar su nombre con el que aparece en la
            página. """
        nombre_titular = self.esperar_elemento('id_denominacion_saldo_gral').text.strip()
        assert \
            nombre_titular == \
            f"Capital de {titular.nombre}:"

    def comparar_titular_de(self, cuenta: Cuenta):
        """ Dada una cuenta, comparar su titular con el que aparece en la
            página. """
        self.comparar_titular(cuenta.titular)

    def comparar_capital_de(self, titular: Titular):
        """ Dado un titular, comparar su capital con el que aparece en la
        página. """
        cap = self.esperar_elemento('id_importe_saldo_gral').text.strip()
        assert cap == float_format(titular.capital)

    def comparar_cuentas_de(self, titular: Titular):
        """ Dado un titular, comparar sus cuentas con las que aparecen en
            la página. """
        divs_cuenta = [
            x.text.strip()
            for x in self.esperar_elementos('class_link_cuenta')
        ]
        slugs_cuenta = [
            x.slug.upper()
            for x in titular.cuentas_interactivas().order_by('slug')
        ]

        assert divs_cuenta == slugs_cuenta

    def crear_movimiento(self, **kwargs):
        self.ir_a_pag(reverse('mov_nuevo'))
        self.completar_form(**kwargs)


def texto_en_hijos_respectivos(
        classname: str,
        lista_elementos: List[MiWebElement | WebElement]
) -> List[str]:
    return [
        x.find_element_by_class_name(classname).text
        for x in lista_elementos
    ]

