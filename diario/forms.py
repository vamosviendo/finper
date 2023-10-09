from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet

from diario.models import CuentaAcumulativa, CuentaInteractiva, Movimiento, Titular
from utils.iterables import hay_mas_de_un_none_en


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

    def clean_slug(self):
        data = self.cleaned_data.get('slug')
        if data.startswith('_'):
            raise forms.ValidationError(
                'No se permite guión bajo inicial en slug', code='guionbajo')

        return data


class FormSubcuenta(forms.Form):
    nombre = forms.CharField()
    slug = forms.CharField()
    saldo = forms.FloatField(required=False)
    titular = forms.ModelChoiceField(
        queryset=Titular.todes(),
        required=False,
        empty_label=None,
    )

    def clean(self):
        self.cleaned_data = super().clean()
        self.cleaned_data['titular'] = \
            self.cleaned_data['titular'] or self.cuenta_madre.titular
        return self.cleaned_data


class FormCrearSubcuenta(forms.Form):
    nombre = forms.CharField()
    slug = forms.CharField()
    titular = forms.ModelChoiceField(
        queryset=Titular.todes(),
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        self.cuenta = CuentaAcumulativa.tomar(slug=kwargs.pop('cuenta'))
        super().__init__(*args, **kwargs)
        self.fields['titular'].initial = self.cuenta.titular_original

    def clean(self):
        self.cleaned_data = super().clean()
        self.cleaned_data['titular'] = \
            self.cleaned_data.get('titular') or self.cuenta.titular_original
        return self.cleaned_data

    def save(self):
        self.cuenta.agregar_subcuenta(
            *[self.cleaned_data[x] for x in self.cleaned_data.keys()],
        )
        return self.cuenta


class FormDividirCuenta(forms.Form):
    form_0_nombre = forms.CharField()
    form_0_slug = forms.CharField()
    form_0_saldo = forms.FloatField(required=False)
    form_0_titular = forms.ModelChoiceField(
        queryset=Titular.todes(),
        required=False,
        empty_label=None,
    )
    form_0_esgratis = forms.BooleanField(
        required=False,
        initial=False
    )
    form_1_nombre = forms.CharField()
    form_1_slug = forms.CharField()
    form_1_saldo = forms.FloatField(required=False)
    form_1_titular = forms.ModelChoiceField(
        queryset=Titular.todes(),
        required=False,
        empty_label=None,
    )
    form_1_esgratis = forms.BooleanField(
        required=False,
        initial=False
    )

    def __init__(self, *args, cuenta, **kwargs):
        super().__init__(*args, **kwargs)
        self.cuenta_madre = CuentaInteractiva.tomar(slug=cuenta)
        self.subcuentas = []
        self.fields['form_0_titular'].initial = self.cuenta_madre.titular
        self.fields['form_1_titular'].initial = self.cuenta_madre.titular

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['form_0_titular'] = \
            cleaned_data.get('form_0_titular') or self.cuenta_madre.titular
        cleaned_data['form_1_titular'] = \
            cleaned_data.get('form_1_titular') or self.cuenta_madre.titular

        self.subcuentas = [{
            'nombre': cleaned_data['form_0_nombre'],
            'slug': cleaned_data['form_0_slug'],
            'saldo': cleaned_data['form_0_saldo'],
            'titular': cleaned_data['form_0_titular'],
            'esgratis': cleaned_data['form_0_esgratis'],
        }, {
            'nombre': cleaned_data['form_1_nombre'],
            'slug': cleaned_data['form_1_slug'],
            'saldo': cleaned_data['form_1_saldo'],
            'titular': cleaned_data['form_1_titular'],
            'esgratis': cleaned_data['form_1_esgratis'],
        }]
        saldos = [dicc.get('saldo') for dicc in self.subcuentas]
        if hay_mas_de_un_none_en(saldos):
            raise ValidationError('Sólo se permite una cuenta sin saldo')

        return self.subcuentas

    def save(self):
        return self.cuenta_madre.dividir_y_actualizar(*self.subcuentas, fecha=None)


class FormMovimiento(forms.ModelForm):

    importe = forms.FloatField()
    esgratis = forms.BooleanField(required=False, initial=False)

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            kwargs['initial'] = {
                'importe': instance.importe,
            }

        super().__init__(*args, **kwargs)

        try:
            if instance.id_contramov is None:
                self.fields['esgratis'].initial = True
        except AttributeError:  # form not bound - instance = None
            pass

        for campo in self.fields.values():
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
        self.instance.esgratis = self.cleaned_data['esgratis']
        return super().save(*args, **kwargs)
