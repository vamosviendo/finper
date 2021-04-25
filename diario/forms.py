from django.forms import ModelForm

from diario.models import Movimiento


class FormMovimiento(ModelForm):

    class Meta:
        model = Movimiento
        fields = ('fecha', 'concepto', 'detalle', 'importe', 'cta_entrada',
                  'cta_salida')
