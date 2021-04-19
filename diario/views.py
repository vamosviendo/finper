from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView, CreateView

from diario.models import Cuenta


def home(request):
    return render(
        request, 'diario/home.html', {'cuentas': Cuenta.objects.all()}
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

