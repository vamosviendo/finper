from django.forms import \
    DateInput, FloatField, ModelForm, NumberInput, TextInput, ValidationError, \
    modelformset_factory

from diario.models import Cuenta, Movimiento


def agregar_clase(campo, clase):
    if campo.widget.attrs.get('class'):
        campo.widget.attrs['class'] += ' form-control'
    else:
        campo.widget.attrs['class'] = 'form-control'


def formset_2_dict_list(data):
    n = 0
    list_regs = list()

    while True:
        dict_reg = {
            k[2]:v for (k,v) in zip(
                [k.split('-') for k in list(data.keys())],
                data.values()
            )
            if k[1] == str(n) and len(k) == 3
        }

        if not dict_reg:
            break

        list_regs.append(dict_reg)
        n += 1

    return list_regs


class FormCuenta(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, campo in self.fields.items():
            agregar_clase(campo, 'form-control')

    class Meta:
        model = Cuenta
        fields = ('nombre', 'slug', )


class FormSubcuenta(ModelForm):

    class Meta:
        model = Cuenta
        fields = ('nombre', 'slug', )

    saldo = FloatField()

    def save(self, *args, **kwargs):
        self.instance.saldo = self.cleaned_data['saldo']
        return super().save(*args, **kwargs)


CuentaFormset = modelformset_factory(Cuenta, form=FormSubcuenta, extra=2)


class FormSubcuentas(CuentaFormset):

    def __init__(self, *args, **kwargs):
        self.cuenta = kwargs.pop('cuenta')
        super().__init__(*args, **kwargs)

    def save(self):
        cta = Cuenta.objects.get(slug=self.cuenta)
        cta.dividir_entre(formset_2_dict_list(self.data))
        return cta


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