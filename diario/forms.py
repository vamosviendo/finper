from django.forms import ModelForm, TextInput, DateInput, NumberInput, ValidationError

from diario.models import Cuenta, Movimiento


def agregar_clase(campo, clase):
    if campo.widget.attrs.get('class'):
        campo.widget.attrs['class'] += ' form-control'
    else:
        campo.widget.attrs['class'] = 'form-control'


class FormCuenta(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, campo in self.fields.items():
            agregar_clase(campo, 'form-control')

    class Meta:
        model = Cuenta
        fields = ('nombre', 'slug', )


class FormSubcuentas(ModelForm):

    class Meta:
        model = Cuenta
        fields = ('nombre', 'slug', 'saldo')


class FormMovimiento(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, campo in self.fields.items():
            agregar_clase(campo, 'form-control')

    class Meta:
        model = Movimiento
        fields = ('fecha', 'concepto', 'detalle', 'importe', 'cta_entrada',
                  'cta_salida', )
        widgets = {
            'detalle': TextInput,
            'fecha': DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'importe': NumberInput(attrs={'step': 0.01}),
        }

    def clean(self):
        cleaned_data = super().clean()
        concepto = cleaned_data.get('concepto')
        if concepto.lower() == 'movimiento correctivo':
            self.add_error(
                'concepto',
                ValidationError(f'El concepto "{concepto}" está reservado '
                                f'para su uso por parte del sistema')
            )
        return cleaned_data