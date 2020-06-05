from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    return HttpResponse('<html><title>Finanzas Personales - Movimientos diarios</title></html>')

