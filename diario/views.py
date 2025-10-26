from __future__ import annotations

from datetime import date
from typing import Any, cast

from django import forms
from django.core.paginator import Paginator
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, \
    UpdateView

from diario.forms import FormCotizacion, FormCuenta, FormMovimiento, \
    FormDividirCuenta, FormCrearSubcuenta, FormTitular, FormMoneda
from diario.models import Cuenta, CuentaInteractiva, CuentaAcumulativa, Dia, \
    Movimiento, Titular, Moneda, Cotizacion
from diario.settings_app import TEMPLATE_HOME
from diario.utils.utils_saldo import saldo_general_historico, verificar_saldos
from utils.tiempo import str2date


def pag_de_fecha(fecha: date, ente: Cuenta | Titular | None) -> int:
    """ Calcula página a partir de fecha """
    queryset = ente.dias() if ente else Dia.con_movimientos()
    posicion = queryset.filter(fecha__gt=fecha).count()
    return (posicion // 7) + 1


class BaseHomeView(TemplateView):
    template_name = TEMPLATE_HOME
    prefijo_url = ""

    def __init__(self, **kwargs: dict[str, Any]):
        super().__init__(**kwargs)
        self.dias_pag = None

    def get_ente(self, kwargs) -> Cuenta | Titular | None:
        """ Debe implementarse en las subclases """
        return None

    def get_url_args(self, ente) -> list:
        """ Debe implementarse en las subclases """
        return []

    def _redirect_con_fecha(self, fecha: str, ente: Cuenta | Titular | None) -> HttpResponseRedirect:
        dias_query = ente.dias() if ente else Dia.con_movimientos()

        dia = dias_query.filter(fecha__lte=fecha).last() or dias_query.first()
        movs = dia.movs(ente=ente)

        while not movs.exists():
            dia = dia.anterior()
            movs = dia.movs(ente=ente)

        page = pag_de_fecha(str2date(fecha), ente)
        args = self.get_url_args(ente)
        args += [movs.last().sk]

        return redirect(
            reverse(f"{self.prefijo_url}movimiento", args=args) + f"?page={page}&redirected=1",
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        fecha = request.GET.get("fecha")
        pag = request.GET.get("page")
        redirected = request.GET.get("redirected")

        ente = self.get_ente(kwargs)
        dias = ente.dias() if ente else Dia.con_movimientos()

        if fecha:
            return self._redirect_con_fecha(fecha, ente)

        self.dias_pag = Paginator(dias.reverse(), 7).get_page(pag)

        movimiento = Movimiento.tomar_o_nada(sk=kwargs.get("sk_mov"))
        condition = (
            (pag and not movimiento) or
            (movimiento and movimiento.dia not in self.dias_pag)
        ) and not redirected

        if condition:
            mov = self.dias_pag[0].movimientos.last()
            url = mov.get_url(ente)
            return redirect(url + f"?page={pag}")

        return super().get(request, *args, **kwargs)

    @staticmethod
    def _get_context_comun(ente: Cuenta | Titular | None, movimiento: Movimiento) -> dict[str, Any]:
        movimiento_en_titulo = \
            f" en movimiento {movimiento.orden_dia} " \
            f"del {movimiento.fecha} ({movimiento.concepto})" \
            if movimiento else ""

        return {
            "movimiento": movimiento,
            "monedas": Moneda.todes(),
            "cuenta": ente if isinstance(ente, Cuenta) else None,
            "titular": ente if isinstance(ente, Titular) else None,
            "filtro": ente,
            "movimiento_en_titulo": movimiento_en_titulo,
        }

    def _get_cuentas(self) -> list[Cuenta]:
        queryset_cuentas = Cuenta.todes().order_by(Lower("nombre"))
        cuentas = []
        for cuenta in queryset_cuentas:
            if cuenta.cta_madre is None:
                self._agregar_cuenta(cuentas, cuenta)
        return cuentas

    def _agregar_cuenta(self, cuentas: list[Cuenta], cuenta: Cuenta):
        cuentas.append(cuenta)
        if cuenta.es_acumulativa:
            cuenta = cast(CuentaAcumulativa, cuenta)
            for cuenta in cuenta.subcuentas.all():
                self._agregar_cuenta(cuentas, cuenta)

    def get_context_especifico(self, ente: Cuenta | Titular | None, movimiento: Movimiento) -> dict[str, Any]:
        movimiento_en_titulo = self._get_context_comun(ente, movimiento)["movimiento_en_titulo"]
        return {
                "saldo_gral":
                    saldo_general_historico(movimiento) if movimiento
                    else sum(c.saldo() for c in Cuenta.filtro(cta_madre=None)),
                "titulo_saldo_gral": f"Saldo general{movimiento_en_titulo}",
                "titulares": Titular.todes(),
                "cuentas": self._get_cuentas(),
            }

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        ente = self.get_ente(kwargs)
        movimiento = Movimiento.tomar_o_nada(sk=kwargs.get("sk_mov"))

        context.update(self._get_context_comun(ente, movimiento))
        context.update(self.get_context_especifico(ente, movimiento))
        context["dias"] = self.dias_pag
        return context


class CuentaHomeView(BaseHomeView):
    prefijo_url = "cuenta_"

    def get_ente(self, kwargs) -> Cuenta:
        return Cuenta.tomar(sk=kwargs.get("sk_cta"))

    def get_url_args(self, ente: Cuenta) -> list[str]:
        return [ente.sk]

    def get_context_especifico(
            self, ente: Cuenta | CuentaInteractiva | CuentaAcumulativa, movimiento: Movimiento) -> dict[str, Any]:
        movimiento_en_titulo = self._get_context_comun(ente, movimiento)["movimiento_en_titulo"]

        return {
            "saldo_gral": ente.saldo(movimiento),
            "titulo_saldo_gral": f"{ente.nombre} (fecha alta: {ente.fecha_creacion}){movimiento_en_titulo}",
            "ancestros": reversed(ente.ancestros()),
            "hermanas": ente.hermanas(),
            "titulares": Titular.filtro(
                sk__in=[x.sk for x in ente.titulares]
            ) if ente.es_acumulativa else Titular.filtro(
                sk=ente.titular.sk
            ),
            "cuentas": ente.subcuentas.all() if ente.es_acumulativa else Cuenta.objects.none(),
        }


class TitularHomeView(BaseHomeView):
    prefijo_url = "titular_"

    def get_ente(self, kwargs) -> Titular:
        return Titular.tomar(sk=kwargs.get("sk"))

    def get_url_args(self, ente: Titular) -> list[str]:
        return [ente.sk]

    def get_context_especifico(self, ente: Titular, movimiento: Movimiento) -> dict[str, Any]:
        movimiento_en_titulo = self._get_context_comun(ente, movimiento)["movimiento_en_titulo"]

        return {
            "saldo_gral": ente.capital(movimiento),
            "titulo_saldo_gral": f"Capital de {ente.nombre}{movimiento_en_titulo}",
            "titulares": Titular.todes(),
            "cuentas": ente.cuentas.all(),
        }


class MovimientoHomeView(BaseHomeView):
    def get_ente(self, kwargs) -> None:
        return None

    def get_context_especifico(self, ente: Cuenta | Titular | None, movimiento: Movimiento) -> dict[str, Any]:
        movimiento_en_titulo = self._get_context_comun(ente, movimiento)["movimiento_en_titulo"]

        return {
            "saldo_gral": saldo_general_historico(movimiento) if movimiento
                else sum(c.saldo() for c in Cuenta.filtro(cta_madre=None)),
            "titulo_saldo_gral": f"Saldo general{movimiento_en_titulo}",
            "titulares": Titular.todes(),
            "cuentas": Cuenta.todes().order_by(Lower("nombre")),
        }


class CuentaMovimientoHomeView(CuentaHomeView):
    pass


class TitularMovimientoHomeView(TitularHomeView):
    pass


class CtaNuevaView(CreateView):
    model = CuentaInteractiva
    form_class = FormCuenta
    template_name = 'diario/cta_form.html'

    def get(self, request, *args, **kwargs):
        if Titular.cantidad() == 0:
            return redirect('tit_nuevo')
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


class CtaElimView(DeleteView):
    model = Cuenta
    slug_url_kwarg = 'sk'
    slug_field = 'sk'

    def get(self, request, *args, **kwargs):
        self.object = cast(Cuenta, self.get_object())
        if cast(Cuenta, self.object).saldo() != 0:
            context = self.get_context_data(
                object=self.object,
                error='No se puede eliminar cuenta con saldo',
            )
            return self.render_to_response(context)

        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


class CtaModView(UpdateView):
    template_name = 'diario/cta_form.html'
    context_object_name = 'cta'
    form_class = FormCuenta
    slug_url_kwarg = 'sk'
    slug_field = 'sk'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.cuenta = Cuenta.tomar(sk=self.kwargs.get('sk'))

    def get_queryset(self):
        if self.cuenta.es_interactiva:
            return CuentaInteractiva.todes()
        else:
            return CuentaAcumulativa.todes()

    def get_form(self, *args, **kwargs):
        formu = super().get_form(*args, **kwargs)
        formu.fields['titular'].disabled = True
        return formu

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


def cta_div_view(request, sk):
    form = None
    if request.method == 'GET':
        form = FormDividirCuenta(cuenta=sk)

    if request.method == 'POST':
        form = FormDividirCuenta(data=request.POST, cuenta=sk)
        if form.is_valid():
            cuenta = form.save()
            return redirect(cuenta)

    return render(request, 'diario/cta_div_form.html', {'form': form})


def cta_agregar_subc_view(request, sk):
    form = None
    if request.method == 'GET':
        form = FormCrearSubcuenta(cuenta=sk)

    if request.method == 'POST':
        form = FormCrearSubcuenta(data=request.POST, cuenta=sk)
        if form.is_valid():
            cuenta = form.save()
            return redirect(cuenta)

    return render(request, 'diario/cta_agregar_subc.html', {'form': form})


class MovNuevoView(CreateView):
    model = Movimiento
    form_class = FormMovimiento
    template_name = 'diario/mov_form.html'

    def get(self, request, *args, **kwargs):
        if Cuenta.cantidad() == 0:
            return redirect('cta_nueva')
        try:
            return super().get(request, *args, **kwargs)
        except AttributeError:
            Dia.crear(fecha=date.today())
            return super().get(request, *args, **kwargs)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)

        cast(forms.ModelChoiceField, form.fields['cta_entrada']).queryset = CuentaInteractiva.todes()
        cast(forms.ModelChoiceField, form.fields['cta_salida']).queryset = CuentaInteractiva.todes()

        return form

    def get_success_url(self):
        next_url = self.request.GET.get("next", reverse("home"))
        if "gya" in self.request.POST:
            return reverse("mov_nuevo")
        return next_url


class MovElimView(DeleteView):
    model = Movimiento
    slug_url_kwarg = 'sk'
    slug_field = 'sk'

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


class MovModView(UpdateView):
    model = Movimiento
    form_class = FormMovimiento
    template_name = 'diario/mov_form.html'
    context_object_name = 'mov'
    slug_url_kwarg = 'sk'
    slug_field = 'sk'

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)

        if self.object.cta_entrada and self.object.cta_entrada.es_acumulativa:
            form.fields['cta_entrada'].disabled = True
        else:
            cast(forms.ModelChoiceField, form.fields['cta_entrada']).queryset = CuentaInteractiva.todes()

        if self.object.cta_salida and self.object.cta_salida.es_acumulativa:
            form.fields['cta_salida'].disabled = True
        else:
            cast(forms.ModelChoiceField, form.fields['cta_salida']).queryset = CuentaInteractiva.todes()

        return form


class MonCotNuevaView(CreateView):
    model = Cotizacion
    form_class = FormCotizacion

    def dispatch(self, request, *args, **kwargs):
        self.moneda = get_object_or_404(Moneda, sk=self.kwargs["sk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["moneda"] = self.moneda
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["moneda"] = self.moneda
        return context

    def form_valid(self, form):
        form.instance.moneda = self.moneda
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.GET.get("next", self.moneda.get_absolute_url())


class CotElimView(DeleteView):
    model = Cotizacion
    slug_url_kwarg = 'sk'
    slug_field = 'sk'

    def get_success_url(self):
        return self.object.moneda.get_absolute_url()


class CotModView(UpdateView):
    model = Cotizacion
    form_class = FormCotizacion
    slug_url_kwarg = 'sk'
    slug_field = 'sk'

    def get_success_url(self):
        return self.object.moneda.get_absolute_url()


class TitularNuevoView(CreateView):
    model = Titular
    template_name = 'diario/tit_form.html'
    form_class = FormTitular

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


class TitElimView(DeleteView):
    model = Titular
    slug_url_kwarg = 'sk'
    slug_field = 'sk'

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


class TitModView(UpdateView):
    model = Titular
    template_name = 'diario/tit_form.html'
    form_class = FormTitular
    slug_url_kwarg = 'sk'
    slug_field = 'sk'

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))

class MonedaView(TemplateView):
    template_name = 'diario/moneda_detalle.html'

    def get(self, request, *args, **kwargs):
        self.page = request.GET.get("page")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["moneda"] = Moneda.tomar(sk=kwargs["sk"])
        context["cotizaciones"] = Paginator(
            context["moneda"].cotizaciones.reverse(), 20
        ).get_page(self.page)
        return context


class MonNuevaView(CreateView):
    model = Moneda
    form_class = FormMoneda
    template_name = 'diario/moneda_form.html'
    success_url = reverse_lazy('home')


class MonModView(UpdateView):
    model = Moneda
    form_class = FormMoneda
    template_name = 'diario/moneda_form.html'
    slug_url_kwarg = 'sk'
    slug_field = 'sk'
    success_url = reverse_lazy('home')


class MonElimView(DeleteView):
    model = Moneda
    slug_url_kwarg = 'sk'
    slug_field = 'sk'
    success_url = reverse_lazy('home')


class CorregirSaldo(TemplateView):
    template_name = 'diario/corregir_saldo.html'

    def get(self, request, *args, **kwargs):
        try:
            self.ctas_erroneas = [
                Cuenta.tomar(sk=c)
                for c in request.GET.get('ctas').split('!')
            ]
        except (AttributeError, Cuenta.DoesNotExist) as BadQuerystringError:
            return redirect(reverse('home'))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'ctas_erroneas': self.ctas_erroneas})
        return context


def verificar_saldos_view(request):
    ctas_erroneas = verificar_saldos()
    if len(ctas_erroneas) > 0:
        sks = '!'.join([c.sk.lower() for c in ctas_erroneas])
        return redirect(f"{reverse('corregir_saldo')}?ctas={sks}")

    return redirect(reverse('home'))


def modificar_saldo_view(request, sk):
    cta_a_corregir = Cuenta.tomar(sk=sk)
    cta_a_corregir.recalcular_saldos_diarios()
    ctas_erroneas = [c.lower() for c in request.GET.get('ctas').split('!')
                               if c != sk.lower()]
    if not ctas_erroneas:
        return redirect(reverse('home'))
    return redirect(
        f"{reverse('corregir_saldo')}?ctas={'!'.join(ctas_erroneas)}")


def agregar_movimiento_view(request, sk):
    cta_a_corregir = CuentaInteractiva.tomar(sk=sk)
    cta_a_corregir.agregar_mov_correctivo()
    ctas_erroneas_restantes = [c.lower() for c in request.GET.get('ctas').split('!')
                               if c != sk.lower()]
    if not ctas_erroneas_restantes:
        return redirect(reverse('home'))

    return redirect(
        f"{reverse('corregir_saldo')}?ctas={'!'.join(ctas_erroneas_restantes)}"
    )
