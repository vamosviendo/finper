from django.db.models.functions import Lower
from django.urls import reverse
from pytest_django import asserts

from diario.models import Movimiento


def test_usa_template_cta_detalle(client, cuenta):
    response = client.get(
        reverse('cta_detalle', args=[cuenta.slug]))
    asserts.assertTemplateUsed(response, 'diario/cta_detalle.html')


def test_pasa_cuenta_a_template(client, cuenta):
    response = client.get(
        reverse('cta_detalle', args=[cuenta.slug]))
    assert response.context['cuenta'] == cuenta
    asserts.assertContains(response, cuenta.nombre)


def test_pasa_subcuentas_a_template(client, cuenta_acumulativa):
    response = client.get(
        reverse('cta_detalle', args=[cuenta_acumulativa.slug])
    )
    assert \
        list(response.context['subcuentas']) == \
        list(cuenta_acumulativa.subcuentas.all())


def test_pasa_subcuentas_ordenadas_por_nombre(client, cuenta):
    cuenta = cuenta.dividir_y_actualizar(
        ['aa', 'zz', 40],
        ['BB', 'YY']
    )

    response = client.get(reverse('cta_detalle', args=[cuenta.slug]))

    assert \
        list(response.context['subcuentas']) == \
        list(cuenta.subcuentas.order_by(Lower('nombre')))


def test_cuenta_interactiva_pasa_titular_a_template(client, cuenta):
    response = client.get(reverse('cta_detalle', args=[cuenta.slug]))
    assert response.context['titulares'] == [cuenta.titular]


def test_cuenta_acumulativa_pasa_titulares_de_subcuentas_a_template(
        client, cuenta_acumulativa, titular, otro_titular):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    sc2.titular = otro_titular
    sc2.save()
    response = client.get(reverse('cta_detalle', args=[cuenta_acumulativa.slug]))
    assert response.context['titulares'] == [titular, otro_titular]


def test_cuenta_interactiva_pasa_lista_vacia_de_subcuentas(client, cuenta):
    response = client.get(reverse('cta_detalle', args=[cuenta.slug]))
    assert list(response.context['subcuentas']) == []


def test_pasa_movimientos_de_cuenta_a_template(client, cuenta, entrada, salida, entrada_otra_cuenta):
    response = client.get(reverse('cta_detalle', args=[cuenta.slug]))
    assert list(response.context['movimientos']) == [entrada, salida]


def test_pasa_movimientos_ordenados_por_fecha(
        client, cuenta, salida_posterior, entrada_tardia, entrada, entrada_temprana):
    response = client.get(reverse('cta_detalle', args=[cuenta.slug]))
    assert \
        list(response.context['movimientos']) == \
        [entrada_temprana, entrada, salida_posterior, entrada_tardia]


def test_pasa_movimientos_de_subcuentas(client, cuenta_acumulativa):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    Movimiento.crear('mov sc1', 30, cta_entrada=sc1)
    Movimiento.crear('mov sc2', 46, cta_entrada=sc2)
    Movimiento.crear('traspaso sc1 sc2', 58, cta_entrada=sc1, cta_salida=sc2)

    response = client.get(
        reverse('cta_detalle', args=[cuenta_acumulativa.slug]))

    assert \
        list(response.context['movimientos']) == \
        list(cuenta_acumulativa.movs())


def test_integrativo_pasa_movs_de_cuenta_a_template(client, cuenta, entrada, salida):
    response = client.get(reverse('cta_detalle', args=[cuenta.slug]))
    asserts.assertContains(response, entrada.concepto)
    asserts.assertContains(response, salida.concepto)
