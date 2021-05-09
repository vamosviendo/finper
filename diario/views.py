import datetime
import os
from pathlib import Path

from django.db.models import Sum
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import \
    CreateView, UpdateView, DeleteView, TemplateView

from diario.forms import FormCuenta, FormMovimiento
from diario.models import Cuenta, Movimiento
from diario.utils import verificar_saldos


def home(request):
    cuentas = Cuenta.todes()

    saldo_gral = cuentas.aggregate(Sum('saldo'))['saldo__sum']

    return render(
        request, 'diario/home.html',
        {
            'cuentas': cuentas,
            'saldo_gral': saldo_gral or 0,
            'ult_movs': Movimiento.todes(),
        }
    )


class HomeView(TemplateView):
    template_name = 'diario/home.html'

    def get(self, request, *args, **kwargs):
        hoy = Path('hoy.mark')
        if (datetime.date.today() >
                datetime.date.fromtimestamp(hoy.stat().st_mtime)):
            ctas_erroneas = verificar_saldos()
            os.utime(
                'hoy.mark',
                (
                    hoy.stat().st_ctime,
                    datetime.datetime.timestamp(datetime.datetime.now())
                )
            )
            if len(ctas_erroneas) > 0:
                full_url = f"{reverse('corregir_saldo')}?ctas="
                full_url += '!'.join([c.slug.lower() for c in ctas_erroneas])
                return redirect(full_url)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        saldo_gral = Cuenta.todes().aggregate(Sum('saldo'))['saldo__sum']

        context.update({
            'cuentas': Cuenta.todes(),
            'ult_movs': Movimiento.todes(),
            'saldo_gral': saldo_gral or 0,
        })

        return context


def cuenta_nueva(request):
    form = FormCuenta()
    if request.method == 'POST':
        form = FormCuenta(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('home'))
    return render(request, 'diario/cta_nueva.html', {'form': form})


class CtaNuevaView(CreateView):
    model = Cuenta
    form_class = FormCuenta
    template_name = 'diario/cta_nueva.html'
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
    template_name = 'diario/cta_mod.html'
    success_url = reverse_lazy('home')


def mov_nuevo(request):
    form = FormMovimiento()
    if request.method == 'POST':
        form = FormMovimiento(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('home'))
    return render(
        request,
        'diario/mov_nuevo.html',
        context={'form': form}
    )


class MovNuevoView(CreateView):
    model = Movimiento
    form_class = FormMovimiento
    template_name = 'diario/mov_nuevo.html'
    success_url = reverse_lazy('home')


class MovElimView(DeleteView):
    model = Movimiento
    success_url = reverse_lazy('home')


class MovModView(UpdateView):
    model = Movimiento
    form_class = FormMovimiento
    template_name = 'diario/mov_mod.html'
    success_url = reverse_lazy('home')


class CorregirSaldo(TemplateView):
    template_name = 'diario/corregir_saldo.html'

    def get(self, request, *args, **kwargs):
        try:
            self.ctas_erroneas = [
                Cuenta.tomar(slug=c.upper())
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
    # cta_a_corregir.refresh_from_db()
    ctas_erroneas = [c.lower() for c in request.GET.get('ctas').split('!')
                               if c != slug.lower()]
    if ctas_erroneas == []:
        return redirect(reverse('home'))
    return redirect(
        f"{reverse('corregir_saldo')}?ctas={'!'.join(ctas_erroneas)}")


def agregar_movimiento_view(request, slug):
    cta_a_corregir = Cuenta.tomar(slug=slug)
    cta_a_corregir.agregar_mov_correctivo()
    # cta_a_corregir.refresh_from_db()
    ctas_erroneas_restantes = [c.lower() for c in request.GET.get('ctas').split('!')
                               if c != slug.lower()]
    if ctas_erroneas_restantes == []:
        return redirect(reverse('home'))

    return redirect(
        f"{reverse('corregir_saldo')}?ctas={'!'.join(ctas_erroneas_restantes)}"
    )