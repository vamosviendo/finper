from django.forms import ModelForm, TextInput, DateInput, NumberInput

from diario.models import Cuenta, Movimiento


class FormCuenta(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs['class'] = 'form-control'

    class Meta:
        model = Cuenta
        fields = ('nombre', )


class FormMovimiento(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if campo.widget.attrs.get('class'):
                campo.widget.attrs['class'] += ' form-control'
            else:
                campo.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Movimiento
        fields = ('fecha', 'concepto', 'detalle', 'importe', 'cta_entrada',
                  'cta_salida', )
        widgets = {
            'detalle': TextInput,
            'fecha': DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'importe': NumberInput(attrs={'step': 0.01}),
        }
