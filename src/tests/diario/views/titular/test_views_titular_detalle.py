from diario.models import Dia
from utils.numeros import float_format


def test_actualiza_context_con_titular(titular, cuenta, cuenta_2, entrada, salida, client):
    response = client.get(titular.get_absolute_url())
    assert response.context['titular'] == titular


def test_pasa_titular_como_filtro(titular, client):
    response = client.get(titular.get_absolute_url())
    assert response.context['filtro'] == titular


def test_pasa_titulares_a_template(titular, otro_titular, client):
    response = client.get(titular.get_absolute_url())
    assert \
        list(response.context['titulares']) == [titular, otro_titular]


def test_pasa_cuentas_del_titular_ordenadas_a_template(
        client, otro_titular, cuenta, cuenta_ajena_2, cuenta_de_dos_titulares):
    sc1, sc2 = cuenta_de_dos_titulares.subcuentas.all()
    cuenta.nombre = "AA",
    cuenta.clean_save()
    cuenta_ajena_2.nombre = "B"
    cuenta_ajena_2.clean_save()
    cuenta_de_dos_titulares.nombre = "C"
    cuenta_de_dos_titulares.clean_save()
    sc1.nombre = "A"
    sc1.clean_save()
    sc2.nombre = "D"
    sc2.clean_save()

    response = client.get(otro_titular.get_absolute_url())
    assert response.context["cuentas"] == [cuenta_ajena_2, cuenta_de_dos_titulares, sc1]


def test_no_pasa_cuentas_inactivas(client, titular, cuenta, cuenta_inactiva):
    response = client.get(titular.get_absolute_url())
    assert cuenta_inactiva not in response.context.get("cuentas")


def test_actualiza_context_con_dias_con_movimientos_del_titular_en_orden_inverso(
        titular, entrada, entrada_anterior, entrada_posterior_otra_cuenta, entrada_tardia_cuenta_ajena, client):
    response = client.get(titular.get_absolute_url())
    assert \
        list(response.context['dias']) == \
        [entrada_posterior_otra_cuenta.dia, entrada.dia, entrada_anterior.dia]


def test_pasa_solo_los_ultimos_7_dias_con_movimientos_del_titular(titular, mas_de_7_dias, client):
    response = client.get(titular.get_absolute_url())
    assert len(response.context['dias']) == 7
    assert mas_de_7_dias.first() not in response.context.get('dias')


def test_si_recibe_movimiento_pasa_titulo_de_saldo_gral_con_titular_y_movimiento(entrada, client):
    titular = entrada.cta_entrada.titular
    response = client.get(titular.get_url_with_mov(entrada))
    assert response.context.get('titulo_saldo_gral') is not None
    assert \
        response.context['titulo_saldo_gral'] == \
        f"Capital de {titular.nombre} en movimiento {entrada.orden_dia} " \
        f"del {entrada.fecha} ({entrada.concepto})"


def test_si_recibe_movimiento_pasa_saldos_de_cuentas_del_titular_en_monedas_al_momento_del_movimiento(
        titular, cuenta, cuenta_2, cuenta_ajena, entrada, salida, traspaso, peso, dolar, client):
    response = client.get(titular.get_url_with_mov(entrada))
    saldos = response.context["saldos_cuentas"]

    assert cuenta_ajena.pk not in saldos.keys()

    assert cuenta.pk in saldos.keys()
    assert saldos[cuenta.pk][peso.sk] == float_format(cuenta.saldo(
        movimiento=entrada)
    )
    # assert saldos[cuenta.pk][dolar.sk] == float_format(cuenta.saldo(
    #     movimiento=entrada, moneda=dolar, compra=True)
    # )

    assert cuenta_2.pk in saldos.keys()
    assert saldos[cuenta_2.pk][peso.sk] == float_format(cuenta_2.saldo(
        movimiento=entrada)
    )
    # assert saldos[cuenta_2.pk][dolar.sk] == float_format(cuenta.saldo(
    #     movimiento=entrada, moneda=dolar, compra=True)
    # )



def test_si_recibe_querydict_con_fecha_calcula_la_pagina_en_base_a_los_movimientos_de_cuentas_del_titular(
        muchos_dias_distintos_titulares, titular, client):
    dia = titular.dias()[6]
    response = client.get(f"{titular.get_absolute_url()}?fecha={str(dia)}", follow=True)
    assert response.context["dias"].number == 4


def test_si_recibe_querydict_con_fecha_muestra_solo_dias_con_movimientos_de_la_cuenta(
        muchos_dias_distintos_titulares, titular, client):
    dias_titular = titular.dias()
    dias_no_titular = [x for x in Dia.todes() if x not in dias_titular]
    dia = dias_titular[4]
    dia_no_titular = dias_no_titular[4]
    response = client.get(f"{titular.get_absolute_url()}?fecha={str(dia)}", follow=True)
    assert dia in response.context["dias"]
    assert dia_no_titular not in response.context["dias"]
