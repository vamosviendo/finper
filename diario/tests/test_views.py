from datetime import date

from django.test import TestCase

from diario.forms import FormMovimiento
from diario.models import Movimiento

from .include import crear_entrada, crear_salida, crear_traspaso


class HomeTest(TestCase):

    def post_movimiento(
            self,
            fecha,
            concepto='',
            detalle='',
            importe='',
            cta_entrada='',
            cta_salida='',
            follow=False
    ):
        return self.client.post(
            '/',
            data={'fecha': fecha,
                  'concepto': concepto,
                  'detalle': detalle,
                  'importe': importe,
                  'cta_entrada': cta_entrada,
                  'cta_salida': cta_salida},
            follow=follow
        )

    def post_movimiento_entrada(self, follow=False):
        return self.post_movimiento(
            fecha=date.today(),
            concepto='Movimiento de entrada',
            detalle='Detalle de entrada',
            importe='1050.00',
            cta_entrada='Efectivo',
            follow=follow
        )

    def post_movimiento_salida(self, follow=False):
        return self.post_movimiento(
            fecha=date.today(),
            concepto='Movimiento de salida',
            detalle='Detalle de salida',
            importe='2000.00',
            cta_salida='Efectivo',
            follow=follow
        )

    def post_movimiento_traspaso(self, follow=False):
        return self.post_movimiento(
            fecha=date.today(),
            concepto='Movimiento de salida',
            detalle='Detalle de salida',
            importe='2000.00',
            cta_entrada='Efectivo',
            cta_salida='Banco',
            follow=follow
        )

    def test_usa_plantilla_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')

    def test_usa_form_movimiento(self):
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], FormMovimiento)

    def test_puede_guardar_un_movimiento(self):
        self.post_movimiento(
            fecha=date(2020, 6, 20),
            concepto='Movimiento de entrada',
            detalle='Detalle de entrada',
            importe='1050.00',
            cta_entrada='Efectivo'
        )
        self.post_movimiento_salida()
        self.assertEqual(Movimiento.objects.count(), 2)
        mov1 = Movimiento.objects.get(id=1)
        mov2 = Movimiento.objects.get(id=2)
        self.assertEqual(mov1.fecha, date(2020, 6, 20))
        self.assertEqual(mov2.fecha, date.today())
        self.assertEqual(mov1.concepto, 'Movimiento de entrada')
        self.assertEqual(mov2.concepto, 'Movimiento de salida')
        self.assertEqual(mov1.detalle, 'Detalle de entrada')
        self.assertEqual(mov2.detalle, 'Detalle de salida')
        self.assertEqual(mov1.importe, 1050)
        self.assertEqual(mov2.importe, 2000)
        self.assertEqual(mov1.cta_entrada, 'Efectivo')
        self.assertEqual(mov2.cta_salida, 'Efectivo')

    def test_post_redirige_a_home(self):
        response = self.post_movimiento_traspaso()
        self.assertRedirects(response, '/')

    def test_pasa_movimientos_a_home_con_get(self):
        crear_entrada()
        crear_salida()
        crear_traspaso()
        response = self.client.get('/')
        for mov in Movimiento.objects.all():
            self.assertContains(response, mov.concepto)

    def test_pasa_movimientos_a_home_con_post(self):
        crear_entrada()
        crear_salida()
        response = self.post_movimiento_traspaso(follow=True)
        for mov in Movimiento.objects.all():
            self.assertContains(response, mov.concepto)

    def test_limpia_form_despues_de_submit(self):
        response = self.post_movimiento_entrada(follow=True)
        formasp = response.context['form'].as_p()

        self.assertNotIn('Sueldo', formasp)
        self.assertNotIn('Detalle sueldo', formasp)
        self.assertNotIn('1050.0', formasp)

    def test_pasa_total_acumulado_a_home_con_post(self):
        response = self.post_movimiento_entrada(follow=True)
        self.assertEqual(response.context['total'], '1050')
        response = self.post_movimiento_salida()
        self.assertEqual(response.context['total'], '-950')

    def test_pasa_fecha_en_formato_apropiado(self):
        response = self.post_movimiento_traspaso(follow=True)
        self.assertIn(date.today().strftime('%d-%m-%Y').encode(), response.content)

    def test_entrada_no_valida_muestra_plantilla_home(self):
        response = self.post_movimiento(fecha=date.today, importe='1260')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'diario/home.html')

    def test_entrada_no_valida_pasa_el_formulario_a_la_plantilla(self):
        response = self.post_movimiento(date.today(), importe='1250')
        self.assertIsInstance(response.context['form'], FormMovimiento)

    def test_muestra_errores_de_validacion_concepto_vacio(self):
        response = self.post_movimiento(date.today(), importe='1250', cta_entrada='Entrada')
        self.assertContains(response, 'Este campo es obligatorio')

    def test_muestra_errores_de_validacion_entrada_y_salida_vacias(self):
        response = self.post_movimiento(
            date.today(),
            concepto='Movimiento nulo',
            detalle='Detalle nulo',
            importe='100',
        )
        self.assertContains(response,
                            'Entrada y salida no pueden ser ambos nulos')

    def test_mantiene_valor_de_campo_correcto_con_entrada_y_salida_vacias(self):
        response = self.post_movimiento(
            date.today(),
            concepto='Movimiento nulo',
            detalle='Detalle nulo',
            importe='100',
        )
        self.assertEqual(response.context['form'].data['concepto'], 'Movimiento nulo')

    def test_pasa_total_acumulado_a_plantilla(self):
        self.post_movimiento_entrada()
        response = self.post_movimiento_salida(follow=True)
        self.assertEqual(response.context['total'], -950)

    # def test_calcula_total_movimiento(self):
    #     pass
    #
    # def test_muestra_total_movimiento(self):
    #     pass
    #
    # def test_POST_redirige_a_home(self):
    #     pass
    #
    # def test_entrada_invalida_no_guarda_movimiento(self):
    #     pass
    #
    # def test_entrada_invalida_muestra_plantilla_home(self):
    #     pass
    #
    # def test_entrada_invalida_pasa_form_a_plantilla(self):
    #     pass
    #
    # def test_entrada_invalida_muestra_mensajes_de_error(self):
    #     pass
    #
    # def test_distintos_tipos_de_error(self):
    #     pass
    #
    # def test_muestra_movimientos_anteriores(self):
    #     pass
    #
    # def test_calcula_total_acumulado(self):
    #     pass