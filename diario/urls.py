"""finper URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from diario import views

urlpatterns = [
    path('c/<slug:ctaname>/', views.HomeView.as_view(), name='cuenta'),
    path('t/<slug:titname>/', views.HomeView.as_view(), name='titular'),
    path('m/<int:pk>', views.HomeView.as_view(), name='movimiento'),
    path('cm/<slug:ctaname>/<int:pk>', views.HomeView.as_view(), name='cuenta_movimiento'),
    path('tm/<slug:titname>/<int:pk>', views.HomeView.as_view(), name='titular_movimiento'),
    path('cta_nueva', views.CtaNuevaView.as_view(), name='cta_nueva'),
    path('cta_elim/<slug:slug>', views.CtaElimView.as_view(), name='cta_elim'),
    path('cta_mod/<slug:slug>', views.CtaModView.as_view(), name='cta_mod'),
    path('cta_div/<slug:slug>', views.cta_div_view, name='cta_div'),
    path('cta_agregar_subc/<slug:slug>', views.cta_agregar_subc_view, name='cta_agregar_subc'),
    path('tit_nuevo', views.TitularNuevoView.as_view(), name='tit_nuevo'),
    path('tit_elim/<slug:titname>', views.TitElimView.as_view(), name='tit_elim'),
    path('tit_mod/<slug:titname>', views.TitModView.as_view(), name='tit_mod'),
    path('mov_nuevo', views.MovNuevoView.as_view(), name='mov_nuevo'),
    path('mov_elim/<int:pk>', views.MovElimView.as_view(), name='mov_elim'),
    path('mov_mod/<int:pk>', views.MovModView.as_view(), name='mov_mod'),
    path('mon_nueva', views.MonNuevaView.as_view(), name='mon_nueva'),
    path('mon_elim/<slug:monname>', views.MonElimView.as_view(), name='mon_elim'),
    path('mon_mod/<slug:monname>', views.MonModView.as_view(), name='mon_mod'),
    # URLs de verificación / corrección de saldos
    path('verificar_saldos', views.verificar_saldos_view, name='verificar_saldos'),
    path('corregir_saldo', views.CorregirSaldo.as_view(), name='corregir_saldo'),
    path('modificar_saldo/<slug:slug>', views.modificar_saldo_view, name='modificar_saldo'),
    path('agregar_movimiento/<slug:slug>', views.agregar_movimiento_view,  name='agregar_movimiento'),
]
