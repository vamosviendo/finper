from diario.models import Dia


class TestDetalleCuenta:
    def test_pasa_cuenta_como_filtro(self, cuenta, client):
        response = client.get(cuenta.get_absolute_url())
        assert response.context['filtro'] == cuenta

    def test_actualiza_context_con_cuenta(self, cuenta, client):
        response = client.get(cuenta.get_absolute_url())
        assert response.context['cuenta'] == cuenta

    def test_si_recibe_sk_de_cuenta_acumulativa_actualiza_context_con_lista_de_titulares_de_subcuentas(
            self, cuenta_de_dos_titulares, client):
        response = client.get(cuenta_de_dos_titulares.get_absolute_url())
        assert list(response.context['titulares']) == cuenta_de_dos_titulares.titulares

    def test_si_recibe_sk_de_cuenta_interactiva_actualiza_context_con_lista_con_nombre_de_titular(
            self, cuenta, client):
        response = client.get(cuenta.get_absolute_url())
        assert list(response.context['titulares']) == [cuenta.titular]

    def test_actualiza_context_con_dias_con_movimientos_de_la_cuenta(
            self, cuenta, entrada, entrada_anterior, entrada_posterior_otra_cuenta, client):
        response = client.get(cuenta.get_absolute_url())
        assert list(response.context['dias']) == [entrada.dia, entrada_anterior.dia]

    def test_pasa_solo_los_ultimos_7_dias_con_movimientos_de_la_cuenta(
            self, cuenta, muchos_dias, client):
        response = client.get(cuenta.get_absolute_url())
        assert len(response.context['dias']) == 7
        assert muchos_dias.first() not in response.context.get('dias')

    def test_pasa_saldo_de_cuenta_como_saldo_general(
            self, cuenta_con_saldo, entrada, client):
        response = client.get(cuenta_con_saldo.get_absolute_url())
        assert response.context['saldo_gral'] == cuenta_con_saldo.saldo()

    def test_pasa_titulo_de_saldo_gral_con_cuenta(self, cuenta, client):
        response = client.get(cuenta.get_absolute_url())
        assert response.context['titulo_saldo_gral'] == f"{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion})"

    def test_si_recibe_id_de_movimiento_pasa_titulo_de_saldo_historico_con_cuenta_y_movimiento(
            self, entrada, client):
        cuenta = entrada.cta_entrada
        response = client.get(cuenta.get_url_with_mov(entrada))
        assert (
            response.context['titulo_saldo_gral'] ==
            f'{cuenta.nombre} (fecha alta: {cuenta.fecha_creacion}) en movimiento {entrada.orden_dia} '
            f'del {entrada.fecha} ({entrada.concepto})')

    def test_si_recibe_querydict_con_fecha_calcula_la_pagina_en_base_a_los_movimientos_de_la_cuenta(
            self, muchos_dias, cuenta, client):
        dia = cuenta.dias()[6]
        response = client.get(f"{cuenta.get_absolute_url()}?fecha={str(dia)}", follow=True)
        assert response.context["dias"].number == 2

    def test_si_recibe_querydict_con_fecha_muestra_solo_dias_con_movimientos_de_la_cuenta(
            self, muchos_dias, cuenta, client):
        dias_cuenta = cuenta.dias()
        dias_no_cuenta = [x for x in Dia.todes() if x not in dias_cuenta]
        dia = dias_cuenta[6]
        dia_no_cuenta = dias_no_cuenta[6]
        response = client.get(f"{cuenta.get_absolute_url()}?fecha={str(dia)}", follow=True)
        assert dia in response.context["dias"]
        assert dia_no_cuenta not in response.context["dias"]

    def test_pasa_subcuentas_de_subcuentas_a_continuacion_de_subcuenta(self, client, cuenta_acumulativa, subsubcuenta):
        sc1, sc2 = cuenta_acumulativa.subcuentas.all()
        ssc11, ssc12 = sc1.subcuentas.all()
        sc1.nombre = "B"
        sc1.clean_save()
        sc2.nombre = "E"
        sc2.clean_save()
        ssc11.nombre = "A"
        ssc11.clean_save()
        ssc12.nombre = "C"
        ssc12.clean_save()

        response = client.get(cuenta_acumulativa.get_absolute_url())
        assert response.context["cuentas"] == [sc1, ssc11, ssc12, sc2]

    def test_no_pasa_subcuentas_inactivas(self, client, cuenta_acumulativa_saldo_0):
        sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
        sc2.activa = False
        sc2.clean_save()

        response = client.get(cuenta_acumulativa_saldo_0.get_absolute_url())
        assert sc2 not in response.context["cuentas"]
