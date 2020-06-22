from django.shortcuts import render

from diario.forms import FormMovimiento


def home(request):
    form = FormMovimiento()
    return render(request, 'diario/home.html', context={'form': form})

