from diario.utils.utils_saldo import saldo_general_historico


def test_pasa_movimiento_a_template(entrada, client):
    response = client.get(entrada.get_absolute_url())
    assert response.context['movimiento'] == entrada


def test_pasa_saldo_general_historico_al_momento_del_movimiento_como_saldo_gral(
        entrada, salida, salida_posterior, client):
    response = client.get(salida.get_absolute_url())
    assert response.context['saldo_gral'] == saldo_general_historico(salida)


def test_pasa_cuentas_independientes(entrada, salida, entrada_otra_cuenta, cuenta_acumulativa, client):
    cuenta = entrada.cta_entrada
    otra_cuenta = entrada_otra_cuenta.cta_entrada
    response = client.get(salida.get_absolute_url())
    assert response.context.get('cuentas') is not None
    assert \
        list(response.context["cuentas"]) == \
        [cuenta, otra_cuenta, cuenta_acumulativa] + list(cuenta_acumulativa.subcuentas.all())


def test_pasa_subcuentas_a_continuacion_de_cuenta_madre(client, entrada, cuenta, cuenta_acumulativa, fecha):
    cuenta.nombre = "A"
    cuenta.clean_save()

    cuenta_acumulativa.nombre = "D"
    cuenta_acumulativa.clean_save()

    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    sc1.nombre = "B"
    sc1.clean_save()
    sc2.nombre = "C"
    sc2.clean_save()

    sc3 = cuenta_acumulativa.agregar_subcuenta("E", "e", cuenta.titular, fecha)

    response = client.get(entrada.get_absolute_url())

    assert list(response.context.get("cuentas")) == [cuenta, cuenta_acumulativa, sc1, sc2, sc3]


def test_no_pasa_cuentas_desactivadas(entrada, cuenta, cuenta_inactiva, cuenta_2, client):
    response = client.get(entrada.get_absolute_url())
    assert cuenta_inactiva not in response.context.get("cuentas")


def test_pasa_titulares(entrada, salida, entrada_cuenta_ajena, client):
    titular = entrada.cta_entrada.titular
    otro_titular = entrada_cuenta_ajena.cta_entrada.titular
    response = client.get(salida.get_absolute_url())
    assert response.context.get('titulares') is not None
    assert list(response.context['titulares']) == [titular, otro_titular]


def test_pasa_titulo_de_saldo_gral_con_movimiento(entrada, client):
    response = client.get(entrada.get_absolute_url())
    assert (
        response.context['titulo_saldo_gral'] ==
        f'Saldo general en movimiento {entrada.orden_dia} '
        f'del {entrada.fecha} ({entrada.concepto})')
