from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView, CreateView

from diario.models import Cuenta, Movimiento


def home(request):
    cuentas = Cuenta.objects.all()
    saldo_gral = 0
    for cuenta in cuentas:
        saldo_gral += cuenta.saldo
    return render(
        request, 'diario/home.html',
        {
            'cuentas': cuentas,
            'saldo_gral': saldo_gral,
            'ult_movs': Movimiento.objects.all(),
        }
    )


class HomeView(TemplateView):
    template_name = 'diario/home.html'


def cuenta_nueva(request):
    if request.method == 'POST':
        Cuenta.objects.create(nombre=request.POST['nombre'])
        return redirect(reverse('home'))
    return render(request, 'diario/cta_nueva.html')


class CtaNuevaView(CreateView):
    model = Cuenta
    fields = []
    template_name = 'diario/cta_nueva.html'

    def get_success_url(self):
        return redirect(reverse('home'))


def mov_nuevo(request):
    try:
        cuenta_entrada = Cuenta.objects.get(pk=request.POST.get('cta_entrada'))
    except Cuenta.DoesNotExist:
        cuenta_entrada = None
    try:
        cuenta_salida = Cuenta.objects.get(pk=request.POST.get('cta_salida'))
    except Cuenta.DoesNotExist:
        cuenta_salida = None
    if request.method == 'POST':
        m = Movimiento(
            fecha=request.POST.get('fecha'),
            concepto=request.POST['concepto'],
            detalle=request.POST.get('detalle'),
            importe=request.POST['importe'],
            cta_entrada=cuenta_entrada,
            cta_salida=cuenta_salida,
        )
        m.full_clean()
        m.save()
        return redirect(reverse('home'))
    return render(
        request,
        'diario/mov_nuevo.html',
        context={'cuentas': Cuenta.objects.all()}
    )
