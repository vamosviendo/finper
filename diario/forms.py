from django import forms
from django.core.exceptions import ValidationError

from diario.models import CuentaAcumulativa, CuentaInteractiva, Movimiento
from utils.listas import hay_mas_de_un_none_en


def agregar_clase(campo, clase):
    if campo.widget.attrs.get('class'):
        campo.widget.attrs['class'] += ' form-control'
    else:
        campo.widget.attrs['class'] = 'form-control'


class FormCuenta(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, campo in self.fields.items():
            agregar_clase(campo, 'form-control')

    class Meta:
        model = CuentaInteractiva
        fields = ('nombre', 'slug', 'titular', )


class FormCuentaAcu(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, campo in self.fields.items():
            agregar_clase(campo, 'form-control')

    class Meta:
        model = CuentaAcumulativa
        fields = ('nombre', 'slug')


class FormSubcuenta(forms.Form):
    nombre = forms.CharField()
    slug = forms.CharField()
    saldo = forms.FloatField(required=False)


CuentaFormset = forms.formset_factory(form=FormSubcuenta, extra=2)


class FormSubcuentas(CuentaFormset):

    def __init__(self, *args, **kwargs):
        self.cuenta = kwargs.pop('cuenta')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data
        saldos = [dicc['saldo'] for dicc in cleaned_data]
        if hay_mas_de_un_none_en(saldos):
            raise ValidationError('Sólo se permite una cuenta sin saldo')

        return cleaned_data

    def save(self):
        cta = CuentaInteractiva.objects.get(slug=self.cuenta)
        cta = cta.dividir_y_actualizar(*self.cleaned_data)
        return cta


class FormMovimiento(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, campo in self.fields.items():
            agregar_clase(campo, 'form-control')

    class Meta:
        model = Movimiento
        fields = ('fecha', 'concepto', 'detalle', 'importe', 'cta_entrada',
                  'cta_salida', )
        widgets = {
            'detalle': forms.TextInput,
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'importe': forms.NumberInput(attrs={'step': 0.01}),
        }

    def clean(self):
        cleaned_data = super().clean()
        concepto = cleaned_data.get('concepto')
        if concepto.lower() == 'movimiento correctivo':
            self.add_error(
                'concepto',
                forms.ValidationError(
                    f'El concepto "{concepto}" está reservado para su uso '
                    f'por parte del sistema'
                )
            )
        return cleaned_data