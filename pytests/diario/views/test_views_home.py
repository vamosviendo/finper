from datetime import timedelta

import pytest
from django.template.response import TemplateResponse
from django.urls import reverse
from pytest_django import asserts
from pytest_django.asserts import assertRedirects

from diario.models import Dia, Movimiento
from diario.settings_app import TEMPLATE_HOME
from diario.utils.utils_saldo import saldo_general_historico


@pytest.fixture
def response(client) -> TemplateResponse:
    return client.get(reverse('home'))


class TestHome:

    def test_usa_template_indicada_en_settings_app(self, client):
        response = client.get('/')
        asserts.assertTemplateUsed(response, template_name=TEMPLATE_HOME)

    def test_pasa_titulares_a_template(self, titular, otro_titular, response):
        assert titular in response.context.get('titulares')
        assert otro_titular in response.context.get('titulares')

    def test_pasa_cuentas_a_template(self, cuenta, cuenta_ajena, response):
        assert cuenta in response.context.get("cuentas")
        assert cuenta_ajena in response.context.get("cuentas")

    def test_pasa_cuentas_ordenadas_por_nombre(self, client, cuenta, cuenta_2, cuenta_ajena):
        cuenta.nombre = 'J'
        cuenta_2.nombre = 'z'
        cuenta_ajena.nombre = 'a'
        for c in cuenta, cuenta_2, cuenta_ajena:
            c.clean_save()
        response = client.get(reverse('home'))
        assert list(response.context.get("cuentas")) == [cuenta_ajena, cuenta, cuenta_2]

    def test_pasa_monedas_a_template(self, peso, dolar, euro, response):
        for moneda in (peso, dolar, euro):
            assert moneda in response.context.get('monedas')

    def test_pasa_dias_a_template(self, dia_con_movs, dia_anterior_con_movs, dia_posterior_con_movs, dia_tardio_con_movs, response):
        for d in (dia_con_movs, dia_anterior_con_movs, dia_posterior_con_movs, dia_tardio_con_movs):
            assert d in response.context.get('dias')

    def test_pasa_dias_ordenados_por_fecha_invertida(
            self, dia_con_movs, dia_anterior_con_movs, dia_posterior_con_movs, dia_tardio_con_movs, response):
        assert response.context.get('dias')[0] == dia_tardio_con_movs

    def test_pasa_solo_los_ultimos_7_dias(self, mas_de_7_dias, response):
        assert len(response.context.get('dias')) == 7
        assert mas_de_7_dias.first() not in response.context.get('dias')

    def test_no_pasa_dias_sin_movimientos(self, dia, dia_anterior, dia_posterior, entrada, salida_posterior, response):
        assert dia_anterior not in response.context.get('dias')

    def test_puede_pasar_movimientos_posteriores(self, mas_de_7_dias, client):
        response = client.get('/?page=2')
        assert mas_de_7_dias.first() in response.context.get('dias')
        assert mas_de_7_dias.last() not in response.context.get('dias')

    def test_incluye_subcuentas_de_cuentas_acumulativas(self, cuenta, cuenta_acumulativa, response):
        cuentas = response.context['cuentas']
        sc1, sc2 = cuenta_acumulativa.arbol_de_subcuentas()
        for c in [cuenta, cuenta_acumulativa, sc1, sc2]:
            assert c in cuentas

    def test_pasa_saldo_general_a_template(
            self, cuenta, cuenta_2, entrada, entrada_otra_cuenta, salida, response):
        assert response.context.get('saldo_gral') == cuenta.saldo() + cuenta_2.saldo()

    def test_pasa_titulo_de_saldo_general_a_template(self, response):
        assert response.context.get('titulo_saldo_gral') is not None
        assert response.context['titulo_saldo_gral'] == "Saldo general"

    def test_considera_solo_cuentas_independientes_para_calcular_saldo_gral(
            self, cuenta, cuenta_2, entrada, entrada_otra_cuenta, salida, client):
        cuenta_2.dividir_entre(
            {'nombre': 'subcuenta 2.1', 'sk': 'sc21', 'saldo': 200},
            {'nombre': 'subcuenta 2.2', 'sk': 'sc22'},
        )
        cuenta_2 = cuenta_2.tomar_del_sk()
        response = client.get(reverse('home'))

        assert response.context['saldo_gral'] == cuenta.saldo() + cuenta_2.saldo()

    def test_si_no_hay_movimientos_pasa_0_a_saldo_general(self, response):
        assert response.context['saldo_gral'] == 0


class TestDetalleCuenta:
    def test_pasa_cuenta_como_filtro(self, cuenta, client):
        response = client.get(reverse('cuenta', args=[cuenta.sk]))
        assert response.context['filtro'] == cuenta

    def test_actualiza_context_con_cuenta(self, cuenta, client):
        response = client.get(reverse('cuenta', args=[cuenta.sk]))
        assert response.context['cuenta'] == cuenta

    def test_si_recibe_sk_de_cuenta_acumulativa_actualiza_context_con_lista_de_titulares_de_subcuentas(
            self, cuenta_de_dos_titulares, client):
        response = client.get(reverse('cuenta', args=[cuenta_de_dos_titulares.sk]))
        assert list(response.context['titulares']) == cuenta_de_dos_titulares.titulares

    def test_si_recibe_sk_de_cuenta_interactiva_actualiza_context_con_lista_con_nombre_de_titular(
            self, cuenta, client):
        response = client.get(reverse('cuenta', args=[cuenta.sk]))
        assert list(response.context['titulares']) == [cuenta.titular]

    def test_actualiza_context_con_dias_con_movimientos_de_la_cuenta(
            self, cuenta, entrada, entrada_anterior, entrada_posterior_otra_cuenta, client):
        response = client.get(reverse('cuenta', args=[cuenta.sk]))
        assert list(response.context['dias']) == [entrada.dia, entrada_anterior.dia]

    def test_pasa_solo_los_ultimos_7_dias_con_movimientos_de_la_cuenta(
            self, cuenta, muchos_dias, client):
        response = client.get(reverse('cuenta', args=[cuenta.sk]))
        assert len(response.context['dias']) == 7
        assert muchos_dias.first() not in response.context.get('dias')

    def test_pasa_saldo_de_cuenta_como_saldo_general(
            self, cuenta_con_saldo, entrada, client):
        response = client.get(reverse('cuenta', args=[cuenta_con_saldo.sk]))
        assert response.context['saldo_gral'] == cuenta_con_saldo.saldo()

    def test_pasa_titulo_de_saldo_gral_con_cuenta(self, cuenta, client):
        response = client.get(reverse('cuenta', args=[cuenta.sk]))
        assert response.context['titulo_saldo_gral'] == f"{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion})"

    def test_si_recibe_id_de_movimiento_pasa_titulo_de_saldo_historico_con_cuenta_y_movimiento(
            self, entrada, client):
        cuenta = entrada.cta_entrada
        response = client.get(reverse('cuenta_movimiento', args=[cuenta.sk, entrada.pk]))
        assert (
            response.context['titulo_saldo_gral'] ==
            f'{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion}) en movimiento {entrada.orden_dia} '
            f'del {entrada.fecha} ({entrada.concepto})')

    def test_si_recibe_querydict_con_fecha_calcula_la_pagina_en_base_a_los_movimientos_de_la_cuenta(
            self, muchos_dias, cuenta, client):
        dia = cuenta.dias()[6]
        response = client.get(f"{reverse('cuenta', args=[cuenta.sk])}?fecha={str(dia)}", follow=True)
        assert response.context["dias"].number == 2

    def test_si_recibe_querydict_con_fecha_muestra_solo_dias_con_movimientos_de_la_cuenta(
            self, muchos_dias, cuenta, client):
        dias_cuenta = cuenta.dias()
        dias_no_cuenta = [x for x in Dia.todes() if x not in dias_cuenta]
        dia = dias_cuenta[6]
        dia_no_cuenta = dias_no_cuenta[6]
        response = client.get(f"{reverse('cuenta', args=[cuenta.sk])}?fecha={str(dia)}", follow=True)
        assert dia in response.context["dias"]
        assert dia_no_cuenta not in response.context["dias"]


class TestDetalleTitular:
    def test_actualiza_context_con_titular(
            self, titular, cuenta, cuenta_2, entrada, salida, client):
        response = client.get(reverse('titular', args=[titular.sk]))
        assert response.context['titular'] == titular

    def test_pasa_titular_como_filtro(self, titular, client):
        response = client.get(reverse('titular', args=[titular.sk]))
        assert response.context['filtro'] == titular

    def test_pasa_titulares_a_template(self, titular, otro_titular, client):
        response = client.get(reverse('titular', args=[titular.sk]))
        assert \
            list(response.context['titulares']) == [titular, otro_titular]

    def test_actualiza_context_con_dias_con_movimientos_del_titular_en_orden_inverso(
            self, titular, entrada, entrada_anterior,
            entrada_posterior_otra_cuenta, entrada_tardia_cuenta_ajena, client):
        response = client.get(reverse('titular', args=[titular.sk]))
        assert \
            list(response.context['dias']) == \
            [entrada_posterior_otra_cuenta.dia, entrada.dia, entrada_anterior.dia]

    def test_pasa_solo_los_ultimos_7_dias_con_movimientos_del_titular(
            self, titular, mas_de_7_dias, client):
        response = client.get(reverse('titular', args=[titular.sk]))
        assert len(response.context['dias']) == 7
        assert mas_de_7_dias.first() not in response.context.get('dias')

    def test_si_recibe_id_de_movimiento_pasa_titulo_de_saldo_gral_con_titular_y_movimiento(
            self, entrada, client):
        titular = entrada.cta_entrada.titular
        response = client.get(
            reverse(
                'titular_movimiento',
                args=[titular.sk, entrada.pk])
        )
        assert response.context.get('titulo_saldo_gral') is not None
        assert \
            response.context['titulo_saldo_gral'] == \
            f"Capital de {titular.nombre} en movimiento {entrada.orden_dia} " \
            f"del {entrada.fecha} ({entrada.concepto})"

    def test_si_recibe_querydict_con_fecha_calcula_la_pagina_en_base_a_los_movimientos_de_cuentas_del_titular(
            self, muchos_dias_distintos_titulares, titular, client):
        # print("Dias titular", *titular.dias(), sep="\n")
        dia = titular.dias()[6]
        response = client.get(f"{reverse('titular', args=[titular.sk])}?fecha={str(dia)}", follow=True)
        assert response.context["dias"].number == 4

    def test_si_recibe_querydict_con_fecha_muestra_solo_dias_con_movimientos_de_la_cuenta(
            self, muchos_dias_distintos_titulares, titular, client):
        dias_titular = titular.dias()
        dias_no_titular = [x for x in Dia.todes() if x not in dias_titular]
        dia = dias_titular[4]
        dia_no_titular = dias_no_titular[4]
        response = client.get(f"{reverse('titular', args=[titular.sk])}?fecha={str(dia)}", follow=True)
        assert dia in response.context["dias"]
        assert dia_no_titular not in response.context["dias"]


class TestDetalleMovimiento:
    def test_pasa_movimiento_a_template(self, entrada, client):
        response = client.get(reverse('movimiento', args=[entrada.pk]))
        assert response.context['movimiento'] == entrada

    def test_pasa_saldo_general_historico_al_momento_del_movimiento_como_saldo_gral(
            self, entrada, salida, salida_posterior, client):
        response = client.get(reverse('movimiento', args=[salida.pk]))
        assert response.context['saldo_gral'] == saldo_general_historico(salida)

    def test_pasa_cuentas_independientes(
            self, entrada, salida, entrada_otra_cuenta, cuenta_acumulativa, client):
        cuenta = entrada.cta_entrada
        otra_cuenta = entrada_otra_cuenta.cta_entrada
        response = client.get(reverse('movimiento', args=[salida.pk]))
        assert response.context.get('cuentas') is not None
        assert \
            list(response.context["cuentas"]) == \
            [cuenta, otra_cuenta, cuenta_acumulativa] + list(cuenta_acumulativa.subcuentas.all())

    def test_pasa_titulares(
            self, entrada, salida, entrada_cuenta_ajena, client):
        titular = entrada.cta_entrada.titular
        otro_titular = entrada_cuenta_ajena.cta_entrada.titular
        response = client.get(reverse('movimiento', args=[salida.pk]))
        assert response.context.get('titulares') is not None
        assert list(response.context['titulares']) == [titular, otro_titular]

    def test_pasa_titulo_de_saldo_gral_con_movimiento(self, entrada, client):
        response = client.get(reverse('movimiento', args=[entrada.pk]))
        assert (
            response.context['titulo_saldo_gral'] ==
            f'Saldo general en movimiento {entrada.orden_dia} '
            f'del {entrada.fecha} ({entrada.concepto})')


class TestBusquedaFecha:
    def test_si_recibe_querydict_con_fecha_busca_pagina_con_la_fecha_recibida(
            self, muchos_dias, dia, client):
        response = client.get(f"/?fecha={str(dia)}", follow=True)
        assert \
            response.context["dias"].number == \
            (Dia.con_movimientos().filter(fecha__gt=dia.fecha).count() // 7) + 1

    def test_si_recibe_querydict_con_fecha_redirige_a_vista_de_detalle_de_movimiento_con_ultimo_movimiento_de_la_fecha(
            self, mas_de_7_dias, client):
        dia = mas_de_7_dias.last()
        mov = dia.movimientos.last()
        response = client.get(f"/?fecha={dia.fecha}")
        asserts.assertRedirects(
            response,
            reverse("movimiento", args=[mov.pk]) + f"?fecha={dia.fecha}&redirected=1"
        )

    def test_si_recibe_querydict_con_fecha_en_vista_de_movimiento_distinto_al_ultimo_de_la_fecha_redirige_a_vista_de_movimiento_con_movimiento_recibido(
            self, mas_de_7_dias, client):
        dia = mas_de_7_dias.last()
        mov = dia.movimientos.last()
        Movimiento.crear("Último movimiento", importe=100, cta_entrada=mov.cta_entrada, dia=dia)
        response = client.get(f"/diario/m/{mov.pk}?fecha={dia.fecha}")
        asserts.assertRedirects(
            response,
            reverse("movimiento", args=[mov.pk]) + f"?fecha={dia.fecha}&redirected=1"
        )

    @pytest.mark.parametrize("origen", ["titular", "cuenta"])
    def test_si_recibe_querydict_con_fecha_en_vista_de_titular_o_cuenta_redirige_a_vista_de_detalle_de_movimiento_en_titular_o_cuenta(
            self, origen, mas_de_7_dias, client, request):
        ente = request.getfixturevalue(origen)
        dia = mas_de_7_dias.last()
        mov = dia.movimientos.last()
        response = client.get(reverse(origen, args=[ente.sk]) + f"?fecha={dia.fecha}")
        asserts.assertRedirects(
            response,
            reverse(f"{origen}_movimiento", args=[ente.sk, mov.pk]) + f"?fecha={dia.fecha}&redirected=1"
        )

    @pytest.mark.parametrize("origen", ["titular", "cuenta"])
    def test_si_recibe_querydict_con_fecha_en_vista_de_titular_o_cuenta_con_movimiento_seleccionado_redirige_a_vista_de_detalle_de_movimiento_en_titular_o_cuenta_con_movimiento_recibido(
            self, origen, mas_de_7_dias, client, request):
        ente = request.getfixturevalue(origen)
        dia = mas_de_7_dias.last()
        mov = dia.movimientos.last()
        Movimiento.crear("Último movimiento", importe=100, cta_entrada=mov.cta_entrada, dia=dia)
        response = client.get(
            reverse(f"{origen}_movimiento", args=[ente.sk, mov.pk]) + f"?fecha={dia.fecha}"
        )
        asserts.assertRedirects(
            response,
            reverse(f"{origen}_movimiento", args=[ente.sk, mov.pk]) + f"?fecha={dia.fecha}&redirected=1"
        )

    def test_si_la_fecha_recibida_en_el_querydict_no_corresponde_a_un_dia_existente_muestra_pagina_con_dias_adyacentes(
            self, muchos_dias, client):
        response1 = client.get("/?fecha=2011-04-21", follow=True)
        response2 = client.get("/?fecha=2011-05-01", follow=True)
        assert response1.context["dias"].number == response2.context["dias"].number

    def test_si_la_fecha_recibida_en_el_querydict_no_corresponde_a_un_dia_existente_selecciona_movimiento_de_ultimo_dia_anterior(
            self, mas_de_7_dias, client):
        dia = mas_de_7_dias.last()
        mov = dia.movimientos.last()
        fecha = dia.fecha + timedelta(1)
        response = client.get(f"/?fecha={fecha}")
        asserts.assertRedirects(
            response,
            reverse("movimiento", args=[mov.pk]) + f"?fecha={dia.fecha}&redirected=1"
        )

    def test_si_la_fecha_recibida_en_el_querydict_corresponde_a_un_dia_sin_movimientos_muestra_pagina_con_dias_adyacentes(
            self, muchos_dias, fecha_tardia, client):
        dia_sin_movs = Dia.tomar(fecha=fecha_tardia - timedelta(1))
        print(dia_sin_movs)
        response1 = client.get(f"/?fecha={dia_sin_movs.fecha}", follow=True)
        response2 = client.get(f"/?fecha={Dia.tomar(fecha=fecha_tardia)}", follow=True)
        assert response1.context["dias"].number == response2.context["dias"].number

    def test_si_la_fecha_recibida_en_el_querydict_corresponde_a_un_dia_sin_movimientos_selecciona_ultimo_movimiento_de_dia_anterior_con_movimientos(
            self, mas_de_7_dias, client):
        dia_anterior = mas_de_7_dias.last()
        assert dia_anterior.movimientos.count() > 0
        mov = dia_anterior.movimientos.last()

        dia_sin_movs = Dia.crear(fecha=dia_anterior.fecha + timedelta(1))
        fecha = dia_sin_movs.fecha
        response = client.get(f"/?fecha={fecha}")
        asserts.assertRedirects(
            response,
            reverse("movimiento", args=[mov.pk]) + f"?fecha={dia_anterior.fecha}&redirected=1"
        )

    @pytest.mark.parametrize("origen", ["titular", "cuenta"])
    def test_si_la_fecha_recibida_en_el_querydict_en_vista_de_titular_o_cuenta_corresponde_a_un_dia_sin_movimientos_de_titular_o_cuenta_muestra_pagina_con_dia_anterior_con_movimientos_de_titular_o_cuenta(
            self, origen, mas_de_7_dias, cuenta_ajena, client, request):
        ente = request.getfixturevalue(origen)
        dia_anterior = mas_de_7_dias.last()
        mov_dia_anterior = dia_anterior.movimientos.last()

        fecha_sin_movs_de_ente = dia_anterior.fecha + timedelta(1)
        Movimiento.crear(
            concepto="Movimiento en día sin movimientos de titular/cuenta",
            importe=100,
            fecha=fecha_sin_movs_de_ente,
            cta_entrada=cuenta_ajena
        )
        Movimiento.crear(
            concepto="Movimiento de otro titular/cuenta en día con movimientos de titular/cuenta",
            importe=100,
            fecha=dia_anterior.fecha,
            cta_entrada=cuenta_ajena
        )

        response = client.get(reverse(origen, args=[ente.sk]) + f"?fecha={fecha_sin_movs_de_ente}")
        asserts.assertRedirects(
            response,
            reverse(
                f"{origen}_movimiento",
                args=[ente.sk, mov_dia_anterior.pk]
            ) + f"?fecha={dia_anterior.fecha}&redirected=1"
        )
