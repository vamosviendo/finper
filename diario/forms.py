from datetime import date
from django import forms


class FormMovimiento(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(auto_id='id_input_%s', *args, **kwargs)

    fecha = forms.DateField(initial=date.today().strftime('%d-%m-%Y'))
    concepto = forms.CharField()
    detalle = forms.CharField()
    entrada = forms.DecimalField()
    salida = forms.DecimalField()

    def as_plist(self):
        return self.as_p().split('\n')
