from __future__ import annotations

from datetime import date
from typing import Any

from django.core.paginator import Paginator
from django.db.models.functions import Lower
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


class HomeView(TemplateView):
    template_name = TEMPLATE_HOME

    #
    # def get(self, request, *args, **kwargs):
    #     hoy = Path('hoy.mark')
    #     if (datetime.date.today() >
    #             datetime.date.fromtimestamp(hoy.stat().st_mtime)):
    #         hoy.touch()
    #         return redirect('verificar_saldos')
    #
    #     return super().get(request, *args, **kwargs)

    def __init__(self, **kwargs: dict[str, Any]):
        super().__init__(**kwargs)
        self.dias_pag = None

    @staticmethod
    def _get_ente_info(request):
        resolver_match = request.resolver_match
        viewname = resolver_match.url_name
        kwargs = resolver_match.kwargs

        if "cuenta" in viewname:
            sk = kwargs.get("sk_cta")
            ente = Cuenta.tomar(sk=sk)
            return {
                "ente": ente,
                "dias": ente.dias(),
                "prefijo": "cuenta_",
                "args": [sk],
            }
        if "titular" in viewname:
            sk = kwargs.get("sk")
            ente = Titular.tomar(sk=sk)
            return {
                "ente": ente,
                "dias": ente.dias(),
                "prefijo": "titular_",
                "args": [sk],
            }
        return {
            "ente": None,
            "dias": Dia.con_movimientos(),
            "prefijo": "",
            "args": [],
        }

    @staticmethod
    def _redirect_con_fecha(fecha, ente_info):
        ente, dias, prefijo, args = tuple(ente_info.values())

        dia = dias.filter(fecha__lte=fecha).last() or dias.first()
        movs = dia.movs(ente=ente)

        while not movs.exists():
            dia = dia.anterior()
            movs = dia.movs(ente=ente)

        page = pag_de_fecha(str2date(fecha), ente)
        args += [movs.last().pk]

        return redirect(
            reverse(f"{prefijo}movimiento", args=args) + f"?page={page}&redirected=1",
        )

    def get(self, request, *args, **kwargs):
        fecha = request.GET.get("fecha")
        pag = request.GET.get("page")
        redirected = request.GET.get("redirected")

        ente_info = self._get_ente_info(request)

        if fecha:
            return self._redirect_con_fecha(fecha, ente_info)

        self.dias_pag = Paginator(ente_info["dias"].reverse(), 7).get_page(pag)

        movimiento = Movimiento.tomar_o_nada(pk=kwargs.get("pk"))
        condition = (
            (pag and not movimiento) or
            (movimiento and movimiento.dia not in self.dias_pag)
        ) and not redirected

        if condition:
            mov = self.dias_pag[0].movimientos.last()
            url = mov.get_url(ente_info["ente"])
            return redirect(url + f"?page={pag}")

        return super().get(request, *args, **kwargs)

    @staticmethod
    def _get_context_comun(**kwargs):
        movimiento = Movimiento.tomar(pk=kwargs["pk"]) if kwargs.get("pk") else None
        cuenta: Cuenta | CuentaInteractiva | CuentaAcumulativa = Cuenta.tomar(sk=kwargs["sk_cta"]) \
            if kwargs.get("sk_cta") else None
        titular = Titular.tomar(sk=kwargs["sk"]) if kwargs.get("sk") else None
        movimiento_en_titulo = \
            f" en movimiento {movimiento.orden_dia} " \
            f"del {movimiento.fecha} ({movimiento.concepto})" \
            if movimiento else ""

        return {
            "movimiento": movimiento,
            "monedas": Moneda.todes(),
            "cuenta": cuenta,
            "titular": titular,
            "filtro": cuenta or titular,
            "movimiento_en_titulo": movimiento_en_titulo,
        }

    def _get_context_especifico(self, context):
        ente: Titular | CuentaInteractiva | CuentaAcumulativa | None = context["filtro"]
        movimiento = context["movimiento"]
        movimiento_en_titulo = context.pop("movimiento_en_titulo")

        if isinstance(ente, Cuenta):
            context_esp = {
                "saldo_gral": ente.saldo(movimiento),
                "titulo_saldo_gral": f"{ente.nombre} (fecha alta: {ente.fecha_creacion}){movimiento_en_titulo}",
                "ancestros": reversed(ente.ancestros()),
                "hermanas": ente.hermanas(),
                "titulares": Titular.filtro(
                    _sk__in=[x.sk for x in ente.titulares]
                ) if ente.es_acumulativa else Titular.filtro(
                    _sk=ente.titular.sk
                ),
                "cuentas": ente.subcuentas.all() if ente.es_acumulativa else Cuenta.objects.none(),
            }

        elif isinstance(ente, Titular):
            context_esp = {
                "saldo_gral": ente.capital(movimiento),
                "titulo_saldo_gral": f"Capital de {ente.nombre}{movimiento_en_titulo}",
                "titulares": Titular.todes(),
                "cuentas": ente.cuentas.all(),
            }
        else:
            context_esp = {
                "saldo_gral":
                    saldo_general_historico(movimiento) if movimiento
                    else sum(c.saldo() for c in Cuenta.filtro(cta_madre=None)),
                "titulo_saldo_gral": f"Saldo general{movimiento_en_titulo}",
                "titulares": Titular.todes(),
                "cuentas": Cuenta.todes().order_by(Lower("nombre")),
            }

        context.update({"dias": self.dias_pag})
        return context_esp

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._get_context_comun(**kwargs))
        context.update(self._get_context_especifico(context))
        return context


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
    slug_field = '_sk'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.saldo() != 0:
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
    slug_field = '_sk'

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
    if request.method == 'GET':
        form = FormDividirCuenta(cuenta=sk)

    if request.method == 'POST':
        form = FormDividirCuenta(data=request.POST, cuenta=sk)
        if form.is_valid():
            cuenta = form.save()
            return redirect(cuenta)

    return render(request, 'diario/cta_div_form.html', {'form': form})


def cta_agregar_subc_view(request, sk):
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

        form.fields['cta_entrada'].queryset = CuentaInteractiva.todes()
        form.fields['cta_salida'].queryset = CuentaInteractiva.todes()

        return form

    def get_success_url(self):
        next_url = self.request.GET.get("next", reverse("home"))
        if "gya" in self.request.POST:
            return reverse("mov_nuevo")
        return next_url


class MovElimView(DeleteView):
    model = Movimiento

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


class MovModView(UpdateView):
    model = Movimiento
    form_class = FormMovimiento
    template_name = 'diario/mov_form.html'
    context_object_name = 'mov'

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)

        if self.object.cta_entrada and self.object.cta_entrada.es_acumulativa:
            form.fields['cta_entrada'].disabled = True
        else:
            form.fields['cta_entrada'].queryset = CuentaInteractiva.todes()

        if self.object.cta_salida and self.object.cta_salida.es_acumulativa:
            form.fields['cta_salida'].disabled = True
        else:
            form.fields['cta_salida'].queryset = CuentaInteractiva.todes()

        return form


class MonCotNuevaView(CreateView):
    model = Cotizacion
    form_class = FormCotizacion

    def dispatch(self, request, *args, **kwargs):
        self.moneda = get_object_or_404(Moneda, _sk=self.kwargs["sk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["moneda"] = self.moneda
        return context

    def form_valid(self, form):
        form.instance.moneda = self.moneda
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


class CotElimView(DeleteView):
    model = Cotizacion


class CotModView(UpdateView):
    model = Cotizacion


class TitularNuevoView(CreateView):
    model = Titular
    template_name = 'diario/tit_form.html'
    form_class = FormTitular

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


class TitElimView(DeleteView):
    model = Titular
    slug_url_kwarg = 'sk'
    slug_field = '_sk'

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))


class TitModView(UpdateView):
    model = Titular
    template_name = 'diario/tit_form.html'
    form_class = FormTitular
    slug_url_kwarg = 'sk'
    slug_field = '_sk'

    def get_success_url(self):
        return self.request.GET.get("next", reverse("home"))

class MonedaView(TemplateView):
    template_name = 'diario/moneda.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["moneda"] = Moneda.tomar(sk=kwargs["sk"])
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
    slug_field = '_sk'
    success_url = reverse_lazy('home')


class MonElimView(DeleteView):
    model = Moneda
    slug_url_kwarg = 'sk'
    slug_field = '_sk'
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
    cta_a_corregir = Cuenta.tomar(sk=sk)
    cta_a_corregir.agregar_mov_correctivo()
    ctas_erroneas_restantes = [c.lower() for c in request.GET.get('ctas').split('!')
                               if c != sk.lower()]
    if not ctas_erroneas_restantes:
        return redirect(reverse('home'))

    return redirect(
        f"{reverse('corregir_saldo')}?ctas={'!'.join(ctas_erroneas_restantes)}"
    )
