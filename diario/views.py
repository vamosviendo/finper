from django.db.models import Sum
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from diario.forms import FormCuenta, FormMovimiento
from diario.models import Cuenta, Movimiento


def home(request):
    cuentas = Cuenta.objects.all()

    saldo_gral = cuentas.aggregate(Sum('saldo'))['saldo__sum']

    return render(
        request, 'diario/home.html',
        {
            'cuentas': cuentas,
            'saldo_gral': saldo_gral or 0,
            'ult_movs': Movimiento.objects.all(),
        }
    )


class HomeView(ListView):
    template_name = 'diario/home.html'
    model = Cuenta
    context_object_name = 'cuentas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        saldo_gral = context.get('cuentas')\
            .aggregate(Sum('saldo'))['saldo__sum']

        context.update({
            'ult_movs': Movimiento.objects.all(),
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
