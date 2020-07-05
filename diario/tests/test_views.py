from datetime import date

from django.test import TestCase

from diario.forms import FormMovimiento
from diario.models import Movimiento


class HomeTest(TestCase):

    def test_usa_plantilla_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')

    def test_usa_form_movimiento(self):
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], FormMovimiento)

    def test_puede_guardar_un_movimiento(self):
        self.client.post(
            '/',
            data={'fecha': date(2020, 6, 20),
                  'concepto': 'Movimiento de entrada',
                  'detalle': 'Detalle de entrada',
                  'entrada': 1050.00}
        )
        self.client.post(
            '/',
            data={'fecha': date.today(),
                  'concepto': 'Movimiento de salida',
                  'detalle': 'Detalle de salida',
                  'salida': 2000.00}
        )
        self.assertEqual(Movimiento.objects.count(), 2)
        mov1 = Movimiento.objects.get(id=1)
        mov2 = Movimiento.objects.get(id=2)
        self.assertEqual(mov1.fecha, date(2020, 6, 20))
        self.assertEqual(mov2.fecha, date.today())
        self.assertEqual(mov1.concepto, 'Movimiento de entrada')
        self.assertEqual(mov2.concepto, 'Movimiento de salida')
        self.assertEqual(mov1.detalle, 'Detalle de entrada')
        self.assertEqual(mov2.detalle, 'Detalle de salida')
        self.assertEqual(mov1.entrada, 1050)
        self.assertEqual(mov2.salida, 2000)

    def test_pasa_movimientos_a_home_con_get(self):
        Movimiento.crear(
            fecha=date.today(),
            concepto='Concepto 1',
            detalle='Detalle 1',
            entrada=100
        )
        Movimiento.crear(
            fecha=date.today(),
            concepto='Concepto 2',
            detalle='Detalle 2',
            entrada=100
        )
        Movimiento.crear(
            fecha=date.today(),
            concepto='Concepto 3',
            entrada=100,
            salida=100
        )
        response = self.client.get('/')

        for mov in Movimiento.objects.all():
            self.assertContains(response, mov.concepto)

    def test_pasa_movimientos_a_home_con_post(self):
        Movimiento.crear(
            fecha=date.today(),
            concepto='Concepto 1',
            detalle='Detalle 1',
            entrada=100
        )
        Movimiento.crear(
            fecha=date.today(),
            concepto='Concepto 2',
            detalle='Detalle 2',
            entrada=100
        )
        response = self.client.post(
            '/',
            data={'fecha': date(2020, 6, 20),
                  'concepto': 'Movimiento de entrada',
                  'detalle': 'Detalle de entrada',
                  'entrada': 1050.00,
                  'salida': 1050.00,
                  }
        )
        for mov in Movimiento.objects.all():
            self.assertContains(response, mov.concepto)

    def test_limpia_form_despues_de_submit(self):
        form = FormMovimiento(
            data={'fecha': date(2020, 6, 20),
                  'concepto': 'Sueldo',
                  'detalle': 'Detalle sueldo',
                  'entrada': 1050.00}
        )

        response = self.client.post('/', form.data)
        formasp = response.context['form'].as_p()

        self.assertNotIn('Sueldo', formasp)
        self.assertNotIn('Detalle sueldo', formasp)
        self.assertNotIn('1050.0', formasp)

    def test_pasa_fecha_en_formato_apropiado(self):
        response = self.client.post(
            '/',
            data={'fecha': date.today(),
                  'concepto': 'Movimiento de entrada',
                  'detalle': 'Detalle de entrada',
                  'entrada': 1050.00,
                  'salida': 1050.00,
                  }
        )
        self.assertIn(date.today().strftime('%d-%m-%Y').encode(), response.content)

    def test_calcula_total_movimiento(self):
        pass

    def test_muestra_total_movimiento(self):
        pass

    def test_POST_redirige_a_home(self):
        pass

    def test_entrada_invalida_no_guarda_movimiento(self):
        pass

    def test_entrada_invalida_muestra_plantilla_home(self):
        pass

    def test_entrada_invalida_pasa_form_a_plantilla(self):
        pass

    def test_entrada_invalida_muestra_mensajes_de_error(self):
        pass

    def test_distintos_tipos_de_error(self):
        pass

    def test_muestra_movimientos_anteriores(self):
        pass

    def test_calcula_total_acumulado(self):
        pass