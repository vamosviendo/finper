from .base import FunctionalTest


class TestValidarMovimiento(FunctionalTest):

    def test_no_se_puede_agregar_movimiento_sin_concepto(self):

        self.browser.find_element_by_id('id_input_entrada').send_keys('5000')
        self.browser.find_element_by_id('id_btn_submit').click()

        self.espera(lambda: self.browser.find_element_by_css_selector(
            '#id_input_concepto:invalid'
        ))
        self.browser.find_element_by_id('id_input_concepto').send_keys('Completando concepto')
        self.browser.find_element_by_id('id_input_entrada').send_keys('5000')
        self.espera(lambda: self.browser.find_element_by_css_selector(
            '#id_input_concepto:valid'
        ))
        self.browser.find_element_by_id('id_btn_submit').click()
        self.esperar_movimiento_en_tabla('Completando concepto')

    def test_no_se_puede_agregar_movimientos_sin_entrada_ni_salida(self):

        # Intento ingresar un movimiento sin importe de entrada ni salida
        self.browser.find_element_by_id('id_input_concepto').send_keys('Movimiento nulo')
        self.browser.find_element_by_id('id_btn_submit').click()

        # El navegador intercepta la petición y no carga el movimiento
        errores = self.espera(
            lambda: self.browser.find_element_by_class_name('has-error')
        )
        self.assertIn('Entrada y salida no pueden ser ambos nulos', errores.text)

        # Completo alguno de los dos campos, el error desaparece y el movimiento
        # es aceptado
        self.browser.find_element_by_id('id_input_concepto').send_keys('Movimiento nulo')
        self.browser.find_element_by_id('id_input_entrada').send_keys('5000')
        self.browser.find_element_by_id('id_btn_submit').click()
        self.esperar_movimiento_en_tabla('Movimiento nulo')
