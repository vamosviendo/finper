from datetime import date
from typing import List

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from diario.models import CuentaAcumulativa, CuentaInteractiva, Movimiento, Titular, Moneda, Dia
from diario.settings_app import TITULAR_PRINCIPAL, MONEDA_BASE

from utils.iterables import hay_mas_de_un_none_en


class FormCuenta(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_creacion'].initial = timezone.now().date()
        self.fields['titular'].initial = Titular.tomar(titname=TITULAR_PRINCIPAL)
        self.fields['moneda'].initial = Moneda.tomar(monname=MONEDA_BASE)
        self.fields['moneda'].required = False

    class Meta:
        model = CuentaInteractiva
        fields = ('nombre', 'slug', 'titular', 'fecha_creacion', 'moneda', )
        widgets = {
            'fecha_creacion': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def clean_slug(self) -> str:
        data = self.cleaned_data.get('slug')
        if data.startswith('_'):
            raise forms.ValidationError(
                'No se permite guión bajo inicial en slug', code='guionbajo')

        return data


class FormCrearSubcuenta(forms.Form):
    fecha = forms.DateField(
        initial=date.today(),
        widget=forms.DateInput(format="%Y-%m-%d", attrs={'type': 'date'})
    )
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
        self.cuenta.agregar_subcuenta(**self.cleaned_data)
        return self.cuenta


class FormDividirCuenta(forms.Form):
    # TODO: Refactor
    fecha = forms.DateField(
        required=False,
        initial=date.today(),
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
    )
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
        self.fecha = None
        self.fields['form_0_titular'].initial = self.cuenta_madre.titular
        self.fields['form_1_titular'].initial = self.cuenta_madre.titular

    def clean(self) -> List[dict]:
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
        self.fecha = cleaned_data['fecha']
        saldos = [dicc.get('saldo') for dicc in self.subcuentas]
        if hay_mas_de_un_none_en(saldos):
            raise ValidationError('Sólo se permite una cuenta sin saldo')

        return self.subcuentas

    def save(self) -> CuentaAcumulativa:
        return self.cuenta_madre.dividir_y_actualizar(
            *self.subcuentas,
            fecha=self.fecha
        )


class FormMovimiento(forms.ModelForm):

    cotizacion = forms.FloatField(required=False, initial=0.0)
    importe = forms.FloatField(
        widget=forms.NumberInput(attrs={'step': 0.01})
    )
    esgratis = forms.BooleanField(required=False, initial=False)
    fecha = forms.DateField(
        initial=Dia.ultima_fecha,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
    )
    moneda = forms.ModelChoiceField(queryset=Moneda.todes(), empty_label=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['importe'].initial = instance.importe
            self.fields['cotizacion'].initial = instance.cotizacion
        self.fields['moneda'].initial = Moneda.tomar(monname=MONEDA_BASE)

        try:
            if instance.id_contramov is None:
                self.fields['esgratis'].initial = True
        except AttributeError:  # form not bound - instance = None
            pass

    class Meta:
        model = Movimiento
        fields = Movimiento.form_fields
        widgets = {
            'detalle': forms.TextInput,
        }

    def clean(self) -> dict:
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

    def save(self, *args, **kwargs) -> Movimiento:

        self.instance.importe = self.cleaned_data['importe']
        self.instance.fecha = self.cleaned_data['fecha']
        self.instance.esgratis = self.cleaned_data['esgratis']
        self.instance.cotizacion = self.cleaned_data['cotizacion'] or 0.0
        return super().save(*args, **kwargs)


class FormTitular(forms.ModelForm):

    class Meta:
        model = Titular
        fields = ('titname', 'nombre', 'fecha_alta')
        widgets = {
            'fecha_alta': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }


class FormMoneda(forms.ModelForm):
    plural = forms.CharField(max_length=100, required=False)
    cotizacion_compra = forms.FloatField(required=False)
    cotizacion_venta = forms.FloatField(required=False)

    class Meta:
        model = Moneda
        fields = ('nombre', 'monname', 'plural', 'cotizacion_compra', 'cotizacion_venta')

    def save(self, *args, **kwargs) -> Moneda:
        self.instance.plural = self.cleaned_data['plural']
        self.instance.cotizacion_compra = self.cleaned_data['cotizacion_compra'] or 1.0
        self.instance.cotizacion_venta = self.cleaned_data['cotizacion_venta'] or 1.0

        return super().save(*args, **kwargs)
