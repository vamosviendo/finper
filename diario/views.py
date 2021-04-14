from django.shortcuts import render
from django.views.generic import TemplateView, View


def home(request):
    return render(request, 'diario/home.html')


class HomeView(TemplateView):
    template_name = 'diario/home.html'


class CtaNuevaView(View):
    pass