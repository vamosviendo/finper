from django.shortcuts import redirect, render

from diario.forms import FormMovimiento
from diario.models import Movimiento


def home(request):
    erroresnodecampo = erroresdecampo = None

    if request.method == 'POST':
        form = FormMovimiento(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
        else:
            erroresnodecampo = form.non_field_errors()
            erroresdecampo = form.errors
    form = FormMovimiento()

    return render(
        request,
        'diario/home.html',
        context={
            'form': form,
            'erroresdecampo': erroresdecampo,
            'erroresnodecampo': erroresnodecampo,
            'movs': Movimiento.objects.all()
        }
    )

