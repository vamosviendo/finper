from datetime import date

from selenium.webdriver.common.by import By

from .base import FunctionalTest
from utils.fechas import hoy


class TestRecorrido(FunctionalTest):

    def test_recorrido_del_sitio(self):

        self.ir_a_pag()

        """ La primera vez que entramos al sitio nos encontramos con:
            - Una sección de totales generales con tres apartados: activo,
                pasivo y saldo. Todos en cero. (1)
            - Una sección de cuentas, vacía. Con solamente un botón para 
                agregar cuentas nuevas. (2)
            - Una lista de últimos movimientos, también vacía, con un botón
                para agregar movimientos. (3)
        """
        # (1) Saldo general:
        total = self.esperar_elemento('id_div_saldo_gral')
        self.assertEqual(
            total.esperar_elemento('id_importe_saldo_gral').text,
            '0.00'
        )

        # (2) Cuentas (vacío):
        grid_cuentas = self.esperar_elemento('id_grid_cuentas')

        # (3) Lista movimientos (vacío)
        lista_ult_movs = self.esperar_elemento('id_lista_ult_movs')
        ult_movs = lista_ult_movs.esperar_elementos('tr', By.TAG_NAME)
        self.assertEqual(len(ult_movs), 1)

        # Lo primero que hacemos es agregar una cuenta a la cual podamos
        # cargarle movimientos.
        self.esperar_elemento('id_btn_cta_nueva').click()
        self.completar('id_nombre', 'Efectivo')
        self.completar('id_slug', 'E')
        self.pulsar()

        # Aparece una caja para la nueva cuenta, con saldo cero
        cuentas = self.esperar_elementos('class_div_cuenta')
        self.assertEqual(len(cuentas), 1)

        self.assertEqual(
            cuentas[0].find_element_by_class_name('class_nombre_cuenta').text,
            'efectivo'
        )
        self.assertEqual(
            cuentas[0].find_element_by_class_name('class_saldo_cuenta').text,
            '0.00'
        )

        # Cargamos saldo a la cuenta por medio de un movimiento
        lista_ult_movs = self.esperar_elemento('id_lista_ult_movs')
        self.pulsar('id_btn_mov_nuevo')

        # El campo fecha tiene por defecto la fecha del día.
        fecha = self.esperar_elemento('id_fecha')
        self.assertEqual(fecha.get_attribute('value'), hoy())
        self.completar('id_concepto', 'Carga de saldo inicial')
        self.completar('id_importe', '985.5')
        self.completar('id_cta_entrada', 'efectivo')
        self.pulsar()
        # cta_entrada = self.esperar_elemento('id_cta_entrada')
        # Select(cta_entrada).select_by_visible_text('Efectivo')

        # El movimiento aparece en la lista de últimos movimientos
        lista_ult_movs = self.esperar_elemento('id_lista_ult_movs')
        ult_movs = lista_ult_movs.find_elements_by_tag_name('tr')
        self.assertEqual(len(ult_movs), 2)   # El encabezado y un movimiento
        self.assertIn(hoy(), ult_movs[1].text)
        self.assertIn('Carga de saldo inicial', ult_movs[1].text)
        self.assertIn('+efectivo', ult_movs[1].text)
        self.assertIn('985.5', ult_movs[1].text)

        # El importe cargado aparece en el campo saldo de la cuenta
        cuenta = self.esperar_elemento('class_div_cuenta', By.CLASS_NAME)
        self.assertEqual(
            cuenta.find_element_by_class_name('class_saldo_cuenta').text,
            '985.50'
        )

        # El importe del movimiento también aparece sumado a activo y a saldo
        # general
        saldo_gral = self.esperar_elemento('id_importe_saldo_gral')
        self.assertEqual(saldo_gral.text, '985.50')

