from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from .models import Movimiento


class FormMovimiento(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(auto_id='id_input_%s', *args, **kwargs)
        self.fields['fecha'].widget.attrs['value'] = \
            date.today().strftime('%d-%m-%Y')
        self.fields['concepto'].widget.attrs['placeholder'] = 'Concepto'
        self.fields['detalle'].widget.attrs['placeholder'] = 'Detalle'
        self.fields['cta_entrada'].widget.attrs['placeholder'] = 'Cta. de entrada'
        self.fields['cta_salida'].widget.attrs['placeholder'] = 'Cta. de salida'

    class Meta:
        model = Movimiento
        fields = '__all__'

    def clean(self):
        datos_limpios = super().clean()
        if datos_limpios['cta_entrada'] is None and datos_limpios['cta_salida'] is None:
            raise ValidationError('Entrada y salida no pueden ser ambos nulos.')
