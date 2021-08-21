import datetime
from pathlib import Path

from django.db.models import Sum
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import \
    DetailView, CreateView, UpdateView, DeleteView, TemplateView

from diario.forms import FormCuenta, FormMovimiento, FormSubcuentas
from diario.models import Cuenta, CuentaInteractiva, Movimiento
from diario.utils import verificar_saldos


class HomeView(TemplateView):
    template_name = 'diario/home.html'

    def get(self, request, *args, **kwargs):
        hoy = Path('hoy.mark')
        if (datetime.date.today() >
                datetime.date.fromtimestamp(hoy.stat().st_mtime)):
            ctas_erroneas = verificar_saldos()

            hoy.touch()

            if len(ctas_erroneas) > 0:
                full_url = f"{reverse('corregir_saldo')}?ctas=" + \
                            '!'.join([c.slug.lower() for c in ctas_erroneas])
                return redirect(full_url)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        saldo_gral = Cuenta.filtro(cta_madre=None)\
                           .aggregate(Sum('_saldo'))['_saldo__sum']

        context.update({
            'cuentas': Cuenta.filtro(cta_madre=None),
            'ult_movs': Movimiento.todes(),
            'saldo_gral': saldo_gral or 0,
        })

        return context


class CtaDetalleView(DetailView):
    model = Cuenta
    template_name = 'diario/cta_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cuenta = self.object.como_subclase()

        context['subcuentas'] = cuenta.subcuentas.all() \
            if cuenta.es_acumulativa \
            else []
        context['movimientos'] = cuenta.movs()

        return context


class CtaNuevaView(CreateView):
    model = CuentaInteractiva
    form_class = FormCuenta
    template_name = 'diario/cta_form.html'
    success_url = reverse_lazy('home')


class CtaElimView(DeleteView):
    model = Cuenta
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.saldo != 0:
            context = self.get_context_data(
                object=self.object,
                error='No se puede eliminar cuenta con saldo',
            )
            return self.render_to_response(context)

        return super().get(request, *args, **kwargs)


class CtaModView(UpdateView):
    model = Cuenta
    form_class = FormCuenta
    template_name = 'diario/cta_form.html'
    success_url = reverse_lazy('home')
    context_object_name = 'cta'


def cta_div_view(request, slug):
    formset = FormSubcuentas(
        cuenta=slug,
    )
    if request.method == 'POST':
        formset = FormSubcuentas(data=request.POST, cuenta=slug)
        if formset.is_valid():
            cuenta = formset.save()
            return redirect(cuenta)

    return render(request, 'diario/cta_div_formset.html', {'formset': formset})


class MovNuevoView(CreateView):
    model = Movimiento
    form_class = FormMovimiento
    template_name = 'diario/mov_form.html'
    success_url = reverse_lazy('home')


class MovElimView(DeleteView):
    model = Movimiento
    success_url = reverse_lazy('home')


class MovModView(UpdateView):
    model = Movimiento
    form_class = FormMovimiento
    template_name = 'diario/mov_form.html'
    success_url = reverse_lazy('home')
    context_object_name = 'mov'


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
