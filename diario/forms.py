from django import forms
from django.core.exceptions import ValidationError

from diario.models import CuentaAcumulativa, CuentaInteractiva, Movimiento
from utils.iterables import hay_mas_de_un_none_en


def agregar_clase(campo, clase):
    if campo.widget.attrs.get('class'):
        campo.widget.attrs['class'] += ' form-control'
    else:
        campo.widget.attrs['class'] = 'form-control'


class FormCuentaInt(forms.ModelForm):

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
        cta = CuentaInteractiva.tomar(slug=self.cuenta)
        cta = cta.dividir_y_actualizar(*self.cleaned_data)
        return cta


class FormCrearSubcuenta(forms.Form):
    nombre = forms.CharField()
    slug = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.cuenta = CuentaAcumulativa.tomar(slug=kwargs.pop('cuenta'))
        super().__init__(*args, **kwargs)

    def save(self):
        self.cuenta.agregar_subcuenta(
            [self.cleaned_data[x] for x in self.cleaned_data.keys()])
        return self.cuenta


class FormMovimiento(forms.ModelForm):

    importe = forms.FloatField()

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            kwargs['initial'].update({'importe': instance.importe})

        super().__init__(*args, **kwargs)

        for _, campo in self.fields.items():
            agregar_clase(campo, 'form-control')

    class Meta:
        model = Movimiento
        fields = ('fecha', 'concepto', 'detalle', 'cta_entrada', 'cta_salida')
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

    def save(self, *args, **kwargs):
        self.instance.importe = self.cleaned_data['importe']
        return super().save(*args, **kwargs)
