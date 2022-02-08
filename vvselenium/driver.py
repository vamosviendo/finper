from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import InvalidElementStateException, \
    NoSuchElementException, UnexpectedTagNameException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select

from .helpers import esperar


class MiWebElement(WebElement):

    def contiene_elemento(self, elemento, criterio=By.ID, debug=False):
        """ Devuelve True si encuentra elemento en obj MiWebElement."""
        if debug:
            print('TEXT:', self.text)
            print('HTML:', self.get_attribute('innerHTML'))

        try:
            self.find_element(criterio, elemento)
            return True
        except NoSuchElementException:
            return False

    def ocupa_espacio(self):
        if self.value_of_css_property("width") in ["0", "0px", "0%"]:
            return False
        if self.value_of_css_property("display") == ("none"):
            return False
        return True

    def es_visible(self):
        if not self.ocupa_espacio():
            return False
        if self.value_of_css_property("opacity") == "0%":
            return False
        if self.value_of_css_property("visibility") == "hidden":
            return False
        if not self.is_displayed():
            return False
        return True

    def int_css_prop(self, cssprop):
        """ Devuelve el valor de una propiedad css numérica como int."""
        return int(self.value_of_css_property(cssprop).rstrip('px%'))

    def innerWidth(self):
        """ Devuelve el ancho interior de un elemento, sin contar
            padding ni border."""
        if self.value_of_css_property('box-sizing') == 'content-box':
            return int(self.size.get('width')) - (
                    self.int_css_prop('padding-left') +
                    self.int_css_prop('padding-right') +
                    self.int_css_prop('border-left-width') +
                    self.int_css_prop('border-right-width')
            )
        else:
            return int(self.size.get('width'))

    def outerWidth(self):
        """ Devuelve el ancho externo de un elemento, incluyendo padding,
            border y margin."""
        if self.value_of_css_property('box-sizing') == 'border-box':
            return int(self.size.get('width')) + (
                    self.int_css_prop('padding-left') +
                    self.int_css_prop('padding-right') +
                    self.int_css_prop('border-left-width') +
                    self.int_css_prop('border-right-width') +
                    self.int_css_prop('margin-left') +
                    self.int_css_prop('margin-right')
            )
        else:
            return int(self.size.get('width')) + (
                    self.int_css_prop('margin-left') +
                    self.int_css_prop('margin-right')
            )

    def img_url(self):
        """ A partir del atributo src de una imagen, devuelve el url
        del campo ImageField correspondiente."""
        src = self.get_attribute('src')
        return urlparse(src).path

    def img_filename(self):
        """ A partir del atributo src de una imagen, devuelve el nombre de
            archivo del campo ImageField correspondiente."""
        return self.img_url()[len('/media/'):]

    @esperar
    def esperar_elemento(self, elemento, criterio=By.ID):
        return self.find_element(criterio, elemento)

    @esperar
    def esperar_elementos(self, selector, criterio=By.CLASS_NAME, fail=True):
        elementos = self.find_elements(criterio, selector)
        if fail:
            assert len(elementos) != 0, \
                f'no se encontraron elementos coincidentes con "{selector}"'
        return elementos

    @esperar
    def esperar_elemento_con_atributo(
            self, selector, atributo, valor, criterio=By.CLASS_NAME):
        elementos = self.find_elements(criterio, selector)
        try:
            return next(
                x for x in elementos if x.get_attribute(atributo) == valor)
        except StopIteration:
            raise AssertionError(
                f'{selector} con {atributo} {valor} no encontrado')

    @esperar
    def esperar_enlace_con_titulo(self, titulo):
        return self.esperar_elemento_con_atributo(
            "a", "title", titulo, By.TAG_NAME)

    def pulsar(self, boton='id_btn_submit', crit=By.ID):
        self.esperar_elemento(boton, crit).click()


class MiFirefox(webdriver.Firefox):
    _web_element_cls = MiWebElement

    def movermouse(self, horiz, vert):
        """ Dispara un movimiento del ratón."""
        webdriver.ActionChains(self).move_by_offset(horiz, vert).perform()

    @esperar
    def esperar_elemento(self, elemento, criterio=By.ID):
        return self.find_element(criterio, elemento)

    @esperar
    def esperar_elementos(self, selector, criterio=By.CLASS_NAME, fail=True):
        elementos = self.find_elements(criterio, selector)
        if fail:
            assert len(elementos) != 0, \
                f'no se encontraron elementos coincidentes con "{selector}"'
        return elementos

    @esperar
    def esperar_que_desaparezca_de_elementos(self, selector, atributo, valor, criterio=By.CLASS_NAME, fail=True):
        elementos = self.find_elements(criterio, selector)
        if fail:
            assert len(elementos) != 0, \
                f'no se encontraron elementos coincidentes con {selector}'

        for elemento in elementos:
            if elemento.get_attribute(atributo) == valor:
                raise AssertionError(
                    f'Elemento con {atributo} {valor} presente')

        return elementos

    @esperar
    def esperar_elemento_con_atributo(
            self, selector, atributo, valor, criterio=By.CLASS_NAME):
        elementos = self.find_elements(criterio, selector)

        try:
            return next(
                x for x in elementos if x.get_attribute(atributo) == valor)
        except StopIteration:
            raise AssertionError(
                f'{selector} con {atributo} {valor} no encontrado')

    def esperar_enlace_con_titulo(self, titulo):
        return self.esperar_elemento_con_atributo(
            "a", "title", titulo, By.TAG_NAME)

    def esperar_opciones_de_campo(self, campo, form=None):
        form = form or self.esperar_elemento('form', By.TAG_NAME)
        try:
            select = form.find_element_by_id(f'id_{campo}')
        except NoSuchElementException:
            select = form.find_element_by_id(f'id_select_{campo}')
        return [x.text for x in select.find_elements_by_tag_name('option')]

    @staticmethod
    def completar_checkbox(checkbox, boolvalue):
        if checkbox.is_selected() != boolvalue:
            checkbox.click()

    def completar(self, id_campo, texto, criterio=By.ID):
        """ Completa un campo de texto en un form, o selecciona un valor
            de un campo select."""
        campo = self.esperar_elemento(id_campo, criterio=criterio)
        try:
            campo.clear()
            campo.send_keys(str(texto))
        except InvalidElementStateException:
            try:
                Select(campo).select_by_visible_text(texto)
            except UnexpectedTagNameException:
                if type(texto) == bool:
                    valor = texto
                elif texto.lower() == 'true':
                    valor = True
                else:
                    valor = False
                self.completar_checkbox(campo, valor)

    def pulsar(self, boton='id_btn_submit', crit=By.ID):
        self.esperar_elemento(boton, crit).click()

    def egresar(self):
        self.esperar_elemento('logout', By.LINK_TEXT).click()
