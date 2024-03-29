from __future__ import annotations

from typing import List
from urllib.parse import urlparse

from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from diario.models import Titular, Cuenta, CuentaInteractiva, CuentaAcumulativa, Movimiento
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
        assert conceptos_mov == [
            x['concepto'] for x in reversed(ente.as_view_context()['movimientos'])
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
        assert cap == float_format(titular.capital)

    def comparar_capital_historico_de(self, titular: Titular, movimiento: Movimiento):
        """ Dado un titular y un movimiento, comparar el capital histórico del
            titular al momento del movimiento con el que aparece como saldo
            general de la página"""
        cap = self.esperar_elemento('id_importe_saldo_gral').text.strip()
        assert cap == float_format(titular.capital_historico(movimiento))

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
        nombre_cuenta = self.esperar_elemento(
            'id_titulo_saldo_gral'
        ).text.strip()
        assert nombre_cuenta == f"Saldo de {cuenta.nombre}:"

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
        assert saldo == float_format(cuenta.saldo)

    def comparar_saldo_historico_de(self, cuenta: Cuenta, movimiento: Movimiento):
        """ Dada una cuenta, comparar su saldo con el que aparece en la página.
        """
        saldo = self.esperar_elemento('id_importe_saldo_gral').text.strip()
        assert saldo == float_format(cuenta.saldo_en_mov(movimiento))

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
    return [
        x.find_element_by_class_name(classname).text
        for x in lista_elementos
    ]

