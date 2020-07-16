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

    def as_plist(self):
        return self.as_p().split('\n')

    def as_pdict(self):
        values = self.as_plist()
        keys = list(self.fields.keys())
        dicc = {}
        for index, value in enumerate(values):
            dicc[keys[index]] = value
        return dicc
