from selenium.webdriver.common.by import By

from diario.models import Cuenta, Movimiento
from .base import FunctionalTest


class TestDetalleCuenta(FunctionalTest):

    def esperar_elementos_especificos(
            self, tipo, elementos, criterio=By.CLASS_NAME):
        lista_elementos = self.esperar_elementos(tipo, criterio)
        self.assertEqual(len(lista_elementos), len(elementos))
        atribs = [x.text for x in lista_elementos]
        for atrib in atribs:
            self.assertIn(atrib, elementos)
        return lista_elementos

    def entrar_en_cuenta(self, link_cuenta):
        nombre = link_cuenta.text
        link_cuenta.click()
        self.assertEqual(
            self.esperar_elemento('id_header_saldo_gral').text,
            nombre
        )

    def test_detalle_de_cuentas(self):

        # Crear cuentas principales
        cta1 = Cuenta.crear('Efectivo', 'e')
        cta2 = Cuenta.crear('Banco', 'b')

        # Cargar saldo a cuentas principales
        Movimiento.crear(
            concepto='Saldo inicial', importe=100, cta_entrada=cta1)
        Movimiento.crear(
            concepto='Saldo inicial', importe=300, cta_entrada=cta2)

        # Dividir cuenta en subcuentas
        cta2.dividir_entre(
            {'nombre': 'Caja de ahorro', 'slug': 'bca', 'saldo': 100, },
            {'nombre': 'Cuenta corriente', 'slug': 'bcc', 'saldo': 200, },
        )
        cta3 = Cuenta.tomar(slug='bca')
        cta4 = Cuenta.tomar(slug='bcc')

        # Movimiento entre cuenta principal (no subdividida) y subcuenta de
        # cuenta principal subdividida
        Movimiento.crear(
            concepto='Extracción bancaria', importe=50,
            cta_entrada=cta1, cta_salida=cta3
        )
        cta2.refresh_from_db()

        # En la página principal no se muestran subcuentas. Sólo cuentas madre
        # o independientes
        self.ir_a_pag()
        cuentas_principales = self.esperar_elementos('class_div_cuenta')
        self.assertEqual(len(cuentas_principales), 2)
        ids_cuentas_principales = [
            x.get_attribute('id') for x in cuentas_principales
        ]
        self.assertIn('id_div_cta_e', ids_cuentas_principales)
        self.assertIn('id_div_cta_b', ids_cuentas_principales)
        self.assertNotIn('id_div_cta_bca', ids_cuentas_principales)
        self.assertNotIn('id_div_cta_bcc', ids_cuentas_principales)

        # El saldo general es suma de cuentas que no dependen de otra (de lo
        # contrario sumaríamos dos veces los importes de subcuentas).
        self.assertEqual(
            self.esperar_elemento('id_importe_saldo_gral').text,
            f'{(cta1.saldo + cta2.saldo):.2f}'
        )

        # Al cliquear en enlace a cuenta, saldo de cuenta toma el lugar del
        # saldo general.
        links_cuenta = self.esperar_elementos('link_cuenta')
        self.entrar_en_cuenta(links_cuenta[1])

        # En la tabla de movimientos se muestran solamente los relacionados
        # con esa cuenta.
        self.esperar_elementos_especificos(
            '.class_row_mov td.class_td_concepto',
            ['Saldo inicial', 'Extracción bancaria'],
            By.CSS_SELECTOR
        )

        # Probamos lo mismo con una cuenta dividida en subcuentas
        self.ir_a_pag()
        links_cuenta = self.esperar_elementos('link_cuenta')
        self.entrar_en_cuenta(links_cuenta[0])

        # En la grilla de cuentas aparecen las subcuentas de 'Banco'
        links_cuenta = self.esperar_elementos_especificos(
            'link_cuenta', ['Caja de ahorro', 'Cuenta corriente'])
        # En la tabla de movimientos se muestran solamente los relacionados
        # con esa cuenta.
        self.esperar_elementos_especificos(
            '.class_row_mov td.class_td_concepto',
            [
                'Saldo inicial',
                'Paso de saldo de Banco a subcuenta Caja de ahorro',
                'Paso de saldo de Banco a subcuenta Cuenta corriente',
                'Extracción bancaria',
            ],
            By.CSS_SELECTOR
        )

        # Finalmente, probamos con una subcuenta de Banco
        self.entrar_en_cuenta(links_cuenta[0])
        # En la tabla de movimientos se muestran solamente los relacionados
        # con esa cuenta.
        self.esperar_elementos_especificos(
            '.class_row_mov td.class_td_concepto',
            [
                'Paso de saldo de Banco a subcuenta Caja de ahorro',
                'Extracción bancaria',
            ],
            By.CSS_SELECTOR
        )
