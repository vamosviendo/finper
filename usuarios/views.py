from django.contrib import auth
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views import View

from usuarios.forms import LoginForm


class Login(LoginView):
    template_name = 'usuarios/login.html'
    authentication_form = LoginForm


class Logout(View):

    def get(self, request):
        auth.logout(request)
        return redirect('/')
