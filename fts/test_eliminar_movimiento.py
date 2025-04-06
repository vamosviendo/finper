from diario.models import Cuenta, Movimiento

from .base import FunctionalTest


class TestEliminaCuenta(FunctionalTest):

    def test_puede_eliminar_movimientos(self):
        """             m1  m2  m3  saldo   -m1  -m3
            cta1 (E)   100      45    145    45    0
            cta2 (CA)      200 -45    155   155  200
        """
        cta1 = Cuenta.crear(nombre='Afectivo', sk='A')
        cta2 = Cuenta.crear(nombre='Caja de ahorro', sk='ca')
        Movimiento.crear(concepto='asaldo', importe=100, cta_entrada=cta1)
        Movimiento.crear(concepto='bsaldo', importe=200, cta_entrada=cta2)
        Movimiento.crear(
            concepto='entrada de efectivo', importe=45,
            cta_entrada=cta1, cta_salida=cta2
        )
        self.ir_a_pag()
        links_mov_elim = self.esperar_elementos('link_elim_mov')
        links_mov_elim[0].click()

        self.esperar_elemento('id_btn_confirm').click()

        movs = self.esperar_elementos('class_row_mov')
        self.assertEqual(len(movs), 2)

        # El importe del movimiento eliminado se descuenta de la cuenta de
        # entrada
        saldo_cta1 = self.esperar_elemento('id_saldo_cta_a')
        self.assertEqual(saldo_cta1.text, '45.00')

        links_mov_elim = self.esperar_elementos('link_elim_mov')
        links_mov_elim[1].click()

        # Si el movimiento tiene cuenta de entrada y de salida, el importe se
        # resta del saldo de la primera y se suma al de la segunda.
        self.esperar_elemento('id_btn_confirm').click()
        saldo_cta1 = self.esperar_elemento('id_saldo_cta_a')
        saldo_cta2 = self.esperar_elemento('id_saldo_cta_ca')
        self.assertEqual(saldo_cta1.text, '0.00')
        self.assertEqual(saldo_cta2.text, '200.00')
