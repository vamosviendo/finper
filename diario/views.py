from django.shortcuts import redirect, render

from diario.forms import FormMovimiento
from diario.models import Movimiento


def home(request):

    errores = False

    if request.method == 'POST':
        form = FormMovimiento(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
        else:
            errores = True

    if not errores:
        form = FormMovimiento()

    return render(
        request,
        'diario/home.html',
        context={
            'form': form,
            'movs': Movimiento.objects.all(),
        }
    )

