from django.shortcuts import redirect, render

from diario.forms import FormMovimiento
from diario.models import Movimiento


def home(request):
    form = FormMovimiento()
    if request.method == 'POST':
        form = FormMovimiento(data=request.POST)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            concepto = form.cleaned_data['concepto']
            detalle = form.cleaned_data['detalle']
            entrada = form.cleaned_data['entrada']
            salida = form.cleaned_data['salida']
            Movimiento.objects.create(
                fecha=fecha,
                concepto=concepto,
                detalle =detalle,
                entrada=entrada,
                salida=salida
            )
            return redirect('/')
    return render(request, 'diario/home.html', context={'form': form})

