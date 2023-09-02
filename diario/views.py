from django.db.models.functions import Lower
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, \
    UpdateView

from diario.forms import FormCuenta, FormMovimiento, FormSubcuentas, \
    FormCrearSubcuenta
from diario.models import Cuenta, CuentaInteractiva, CuentaAcumulativa, \
    Movimiento, Titular
from diario.utils import saldo_general_historico, verificar_saldos


class HomeView(TemplateView):
    template_name = 'diario/home.html'

    #
    # def get(self, request, *args, **kwargs):
    #     hoy = Path('hoy.mark')
    #     if (datetime.date.today() >
    #             datetime.date.fromtimestamp(hoy.stat().st_mtime)):
    #         hoy.touch()
    #         return redirect('verificar_saldos')
    #
    #     return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movimiento = None if kwargs.get('pk') is None \
            else Movimiento.tomar(pk=kwargs['pk'])
        cuenta = None if kwargs.get('ctaname') is None \
            else Cuenta.tomar(slug=kwargs['ctaname'])
        titular = None if kwargs.get('titname') is None \
            else Titular.tomar(titname=kwargs['titname'])
        movimiento_en_titulo = "" if movimiento is None \
            else f" histórico en movimiento {movimiento.orden_dia} " \
                 f"del {movimiento.fecha} ({movimiento.concepto})"

        context['titulo_saldo_gral'] = 'Saldo general'

        if cuenta:
            context.update(cuenta.as_template_context(
                movimiento, es_elemento_principal=True
            ))

        elif titular:
            context.update({
                'titulares': [
                    x.as_template_context(movimiento)
                    for x in Titular.todes()
                ]
            })
            context.update(titular.as_template_context(
                    movimiento, es_elemento_principal=True
            ))

        elif movimiento:
            context.update({
                'titulo_saldo_gral': f'Saldo general{movimiento_en_titulo}',
                'saldo_gral': saldo_general_historico(movimiento),
                'titulares': [x.as_template_context(movimiento) for x in Titular.todes()],
                'cuentas': [
                    x.as_template_context(movimiento) for x in
                    Cuenta.filtro(cta_madre=None).order_by(Lower('nombre'))
                ],
                'movimientos': Movimiento.todes(),
                'movimiento': movimiento,
            })

        else:
            context.update({
                'saldo_gral':
                    sum([c.saldo for c in Cuenta.filtro(cta_madre=None)]),
                'titulares': Titular.todes(),
                'cuentas': [
                    x.as_template_context() for x in
                    Cuenta.filtro(cta_madre=None).order_by(Lower('nombre'))
                ],
                'movimientos': Movimiento.todes(),
            })

        return context


class CtaNuevaView(CreateView):
    model = CuentaInteractiva
    form_class = FormCuenta
    template_name = 'diario/cta_form.html'
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        if Titular.cantidad() == 0:
            return redirect('tit_nuevo')
        return super().get(request, *args, **kwargs)


class CtaElimView(DeleteView):
    model = Cuenta

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.saldo != 0:
            context = self.get_context_data(
                object=self.object,
                error='No se puede eliminar cuenta con saldo',
            )
            return self.render_to_response(context)

        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('home')


class CtaModView(UpdateView):
    template_name = 'diario/cta_form.html'
    success_url = reverse_lazy('home')
    context_object_name = 'cta'
    form_class = FormCuenta

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.cuenta = Cuenta.tomar(slug=self.kwargs.get('slug'))

    def get_queryset(self):
        if self.cuenta.es_interactiva:
            return CuentaInteractiva.todes()
        else:
            return CuentaAcumulativa.todes()

    def get_form(self, *args, **kwargs):
        formu = super().get_form(*args, **kwargs)
        formu.fields['titular'].disabled = True
        return formu


def cta_div_view(request, slug):
    global formset
    if request.method == 'GET':
        formset = FormSubcuentas(cuenta=slug)

    if request.method == 'POST':
        formset = FormSubcuentas(data=request.POST, cuenta=slug)
        if formset.is_valid():
            cuenta = formset.save()
            return redirect(cuenta)

    return render(request, 'diario/cta_div_formset.html', {'formset': formset})


def cta_agregar_subc_view(request, slug):
    global form
    if request.method == 'GET':
        form = FormCrearSubcuenta(cuenta=slug)

    if request.method == 'POST':
        form = FormCrearSubcuenta(data=request.POST, cuenta=slug)
        if form.is_valid():
            cuenta = form.save()
            return redirect(cuenta)

    return render(request, 'diario/cta_agregar_subc.html', {'form': form})


class MovNuevoView(CreateView):
    model = Movimiento
    form_class = FormMovimiento
    template_name = 'diario/mov_form.html'
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        if Cuenta.cantidad() == 0:
            return redirect('cta_nueva')
        return super().get(request, *args, **kwargs)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)

        form.fields['cta_entrada'].queryset = CuentaInteractiva.todes()
        form.fields['cta_salida'].queryset = CuentaInteractiva.todes()

        return form


class MovElimView(DeleteView):
    model = Movimiento
    success_url = reverse_lazy('home')


class MovModView(UpdateView):
    model = Movimiento
    form_class = FormMovimiento
    template_name = 'diario/mov_form.html'
    success_url = reverse_lazy('home')
    context_object_name = 'mov'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)

        if self.object.cta_entrada and self.object.cta_entrada.es_acumulativa:
            form.fields['cta_entrada'].disabled = True
        else:
            form.fields['cta_entrada'].queryset = CuentaInteractiva.todes()

        if self.object.cta_salida and self.object.cta_salida.es_acumulativa:
            form.fields['cta_salida'].disabled = True
        else:
            form.fields['cta_salida'].queryset = CuentaInteractiva.todes()

        return form


class TitularNuevoView(CreateView):
    model = Titular
    fields = ['titname', 'nombre']
    template_name = 'diario/tit_form.html'
    success_url = '/'


class TitElimView(DeleteView):
    model = Titular
    slug_url_kwarg = 'titname'
    slug_field = 'titname'
    success_url = reverse_lazy('home')


class TitModView(UpdateView):
    model = Titular
    template_name = 'diario/tit_form.html'
    slug_url_kwarg = 'titname'
    slug_field = 'titname'
    success_url = reverse_lazy('home')
    fields = ['titname', 'nombre']


class CorregirSaldo(TemplateView):
    template_name = 'diario/corregir_saldo.html'

    def get(self, request, *args, **kwargs):
        try:
            self.ctas_erroneas = [
                Cuenta.tomar(slug=c)
                for c in request.GET.get('ctas').split('!')
            ]
        except (AttributeError, Cuenta.DoesNotExist) as BadQuerystringError:
            return redirect(reverse('home'))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'ctas_erroneas': self.ctas_erroneas})
        return context


def verificar_saldos_view(request):
    ctas_erroneas = verificar_saldos()
    if len(ctas_erroneas) > 0:
        slugs = '!'.join([c.slug.lower() for c in ctas_erroneas])
        return redirect(f"{reverse('corregir_saldo')}?ctas={slugs}")

    return redirect(reverse('home'))


def modificar_saldo_view(request, slug):
    cta_a_corregir = Cuenta.tomar(slug=slug)
    cta_a_corregir.corregir_saldo()
    ctas_erroneas = [c.lower() for c in request.GET.get('ctas').split('!')
                               if c != slug.lower()]
    if not ctas_erroneas:
        return redirect(reverse('home'))
    return redirect(
        f"{reverse('corregir_saldo')}?ctas={'!'.join(ctas_erroneas)}")


def agregar_movimiento_view(request, slug):
    cta_a_corregir = Cuenta.tomar(slug=slug)
    cta_a_corregir.agregar_mov_correctivo()
    ctas_erroneas_restantes = [c.lower() for c in request.GET.get('ctas').split('!')
                               if c != slug.lower()]
    if not ctas_erroneas_restantes:
        return redirect(reverse('home'))

    return redirect(
        f"{reverse('corregir_saldo')}?ctas={'!'.join(ctas_erroneas_restantes)}"
    )
