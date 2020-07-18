from django.shortcuts import redirect, render

from diario.forms import FormMovimiento
from diario.models import Movimiento


def home(request):
    errores = None
    if request.method == 'POST':
        form = FormMovimiento(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
        else:
            errores = form.errors
    form = FormMovimiento()
    return render(
        request,
        'diario/home.html',
        context={'form': form, 'errores': errores, 'movs': Movimiento.objects.all()}
    )

