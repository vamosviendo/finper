from selenium.webdriver.common.by import By

from vvsteps.driver import MiFirefox


class FinperFirefox(MiFirefox):

    # TODO: ¿pasar a MiFirefox?
    def __init__(self, base_url=None):
        super().__init__()
        self.base_url = base_url

    # TODO: pasar a MiFirefox
    def ir_a_pag(self, url: str = ''):
        self.get(f"{self.base_url}{url}")

    def cliquear_en_cuenta(self, cuenta):
        self.esperar_elemento(cuenta.slug.upper(), By.LINK_TEXT).click()

    def esperar_movimiento(self, columna, contenido):
        movimientos = self.esperar_elementos('class_row_mov', By.CLASS_NAME)
        try:
            return next(
                x for x in movimientos
                if x.find_element_by_class_name(f'class_td_{columna}').text
                    == contenido
            )
        except StopIteration:
            raise ValueError(
                f'Contenido {contenido} no encontrado en columna {columna}'
            )

    def comparar_movimientos(self, cuenta):
        """ Dada una cuenta, comparar sus movimientos con los que aparecen en
            la página. """
        conceptos_mov = [
            x.text for x in self.esperar_elementos(
                '.class_row_mov td.class_td_concepto', By.CSS_SELECTOR
        )]
        assert conceptos_mov == list(
            reversed(
                [x.concepto for x in cuenta.movs()]
            )
        )

    def comparar_titular(self, cuenta):
        """ Dada una cuenta, comparar su titular con el que aparece en la
            página. """
        nombre_titular = self.esperar_elemento(
            'class_div_nombre_titular', By.CLASS_NAME
        ).text.strip()
        assert nombre_titular == cuenta.titular.nombre
