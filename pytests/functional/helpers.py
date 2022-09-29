from selenium.webdriver.common.by import By

from vvsteps.driver import MiFirefox


class FinperFirefox(MiFirefox):

    # TODO: ¿pasar a MiFirefox?
    def __init__(self, base_url=None):
        super().__init__()
        self.base_url = base_url

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

    # TODO: pasar a MiFirefox
    def ir_a_pag(self, url: str = ''):
        self.get(f"{self.base_url}{url}")
