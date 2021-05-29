from diario.models import Cuenta, Movimiento
from .base import FunctionalTest


class TestDetalleCuenta(FunctionalTest):

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
        cta2.dividir_entre([
            {'nombre': 'Caja de ahorro', 'slug': 'bca', 'saldo': 100, },
            {'nombre': 'Cuenta corriente', 'slug': 'bcc', 'saldo': 200, },
        ])
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
        links_cuenta[1].click()
        self.assertEqual(
            self.esperar_elemento('id_header_saldo_gral').text,
            'Efectivo'
        )
        # En la tabla de movimientos se muestran solamente los relacionados
        # con esa cuenta.
        movimientos = self.esperar_elementos('class_row_mov')
        self.assertEqual(len(movimientos), 2)
        conceptos = [
            x.find_element_by_css_selector('td.class_td_concepto').text
            for x in movimientos
        ]
        self.assertEqual(conceptos[0], 'Saldo inicial')
        self.assertEqual(conceptos[1], 'Extracción bancaria')
