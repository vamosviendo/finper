from datetime import date
from django import forms

from .models import Movimiento


class FormMovimiento(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(auto_id='id_input_%s', *args, **kwargs)
        self.fields['fecha'].widget.attrs['value'] = \
            date.today().strftime('%d-%m-%Y')
        self.fields['concepto'].widget.attrs['placeholder'] = 'Concepto'
        self.fields['detalle'].widget.attrs['placeholder'] = 'Detalle'

    class Meta:
        model = Movimiento
        fields = '__all__'
