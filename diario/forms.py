from datetime import date
from django import forms


class FormMovimiento(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(auto_id='id_input_%s', *args, **kwargs)

    fecha = forms.DateField(initial=date.today().strftime('%d-%m-%Y'))
    concepto = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Concepto'})
    )
    detalle = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Detalle'}),
        required=False
    )
    entrada = forms.DecimalField(required=False)
    salida = forms.DecimalField(required=False)

    def as_plist(self):
        return self.as_p().split('\n')

    def as_pdict(self):
        values = self.as_plist()
        keys = list(self.fields.keys())
        dicc = {}
        for index, value in enumerate(values):
            dicc[keys[index]] = value
        return dicc
