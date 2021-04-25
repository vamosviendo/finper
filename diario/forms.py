from django.forms import ModelForm, TextInput, DateInput, NumberInput

from diario.models import Cuenta, Movimiento


class FormCuenta(ModelForm):

    class Meta:
        model = Cuenta
        fields = ('nombre', )


class FormMovimiento(ModelForm):

    class Meta:
        model = Movimiento
        fields = ('fecha', 'concepto', 'detalle', 'importe', 'cta_entrada',
                  'cta_salida', )
        widgets = {
            'detalle': TextInput,
            'fecha': DateInput(format='%Y%m%d', attrs={'type': 'date'}),
            'importe': NumberInput(attrs={'step': 0.01}),
        }