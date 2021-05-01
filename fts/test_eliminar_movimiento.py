from diario.models import Cuenta, Movimiento

from .base import FunctionalTest


class TestEliminaCuenta(FunctionalTest):

    def test_puede_eliminar_movimientos(self):
        cta1 = Cuenta.objects.create(nombre='Efectivo', slug='E')
        cta2 = Cuenta.objects.create(nombre='Caja de ahorro', slug='ca')
        Movimiento.objects.create(
            concepto='saldo', importe=100, cta_entrada=cta1)
        Movimiento.objects.create(
            concepto='saldo', importe=200, cta_entrada=cta2
        )
        Movimiento.objects.create(
            concepto='entrada de efectivo',
            importe=45, cta_entrada=cta1, cta_salida=cta2
        )
        self.browser.get(self.live_server_url)
        links_mov_elim = self.esperar_elementos('link_elim_mov')
        links_mov_elim[0].click()

        self.esperar_elemento('id_btn_confirm').click()

        movs = self.esperar_elementos('class_row_mov')
        self.assertEqual(len(movs), 2)

        # El importe del movimiento eliminado se descuenta de la cuenta de
        # entrada
        saldo_cta1 = self.browser.find_element_by_id('id_saldo_cta_e')
        self.assertEqual(saldo_cta1.text, '45.00')

        links_mov_elim = self.esperar_elementos('link_elim_mov')
        links_mov_elim[1].click()

        # Si el movimiento tiene cuenta de entrada y de salida, el importe se
        # resta del saldo de la primera y se suma al de la segunda.
        self.esperar_elemento('id_btn_confirm').click()
        saldo_cta1 = self.browser.find_element_by_id('id_saldo_cta_e')
        saldo_cta2 = self.browser.find_element_by_id('id_saldo_cta_ca')
        self.assertEqual(saldo_cta1.text, '0.00')
        self.assertEqual(saldo_cta2.text, '200.00')