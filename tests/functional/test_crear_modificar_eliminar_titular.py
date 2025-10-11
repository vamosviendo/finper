import pytest
from django.urls import reverse


def test_crear_titular(browser, fecha):
    """ Cuando vamos a la página de titular nuevo y completamos el formulario,
        aparece un titular nuevo entre los titulares del sitio. """
    browser.ir_a_pag(reverse("tit_nuevo"))
    browser.completar_form(
        nombre="titular nuevo",
        sk="tn",
        fecha_alta=fecha,
    )
    browser.assert_url(reverse("home"))

    # Vemos que la cuenta creada aparece entre las cuentas de la página de
    # inicio
    nombre_titular = browser.encontrar_elemento('id_link_tit_tn').text.strip()
    assert nombre_titular == "titular nuevo"


def test_modificar_titular(browser, titular, fecha_anterior):
    """ Cuando vamos a la página de modificar titular y completamos el
        formulario, vemos el titular modificado en la página principal """
    browser.ir_a_pag(titular.get_edit_url())

    # En todos los campos del formulario aparece el valor del campo correspondiente del titular:
    browser.controlar_modelform(instance=titular)

    browser.completar_form(
        nombre="titular con nombre modificado",
        sk="tcnm",
        fecha_alta=fecha_anterior,
    )
    browser.assert_url(reverse('home'))

    nombre_titular = browser.encontrar_elemento('id_link_tit_tcnm').text.strip()
    assert nombre_titular == "titular con nombre modificado"


@pytest.mark.parametrize("origen", ["/", "/diario/c/c/", "/diario/m/", "/diario/cm/c/"])
@pytest.mark.parametrize("destino", ["id_link_titular_nuevo", "id_link_tit_mod_"])
def test_crear_o_modificar_titular_redirige_a_pagina_desde_donde_se_invoco(
        browser, origen, destino, titular, cuenta, fecha, entrada, entrada_anterior):
    if "m/" in origen:
        origen = f"{origen}{entrada_anterior.sk}"
    if destino == "id_link_tit_mod_":
        destino = f"{destino}{titular.sk}"
    browser.ir_a_pag(origen)
    browser.pulsar(destino)
    browser.completar_form(
        nombre="titular nuevo",
        sk="tn",
        fecha_alta=fecha,
    )
    browser.assert_url(origen)

@pytest.mark.parametrize("origen", [None, "titular", "cuenta"])
@pytest.mark.parametrize("destino", ["id_link_titular_nuevo", "id_link_tit_mod_"])
def test_crear_o_modificar_titular_desde_pagina_posterior_redirige_a_esa_pagina_con_el_ultimo_movimiento_seleccionado(
        browser, titular, fecha, mas_de_7_dias, origen, destino, request):
    if origen:
        ente = request.getfixturevalue(origen)
        url_origen = ente.get_absolute_url()
        dias = list(ente.dias())
    else:
        ente = None
        url_origen = reverse("home")
        dias = list(mas_de_7_dias)
    movimiento = dias[-8].movimientos.last()
    url_final = movimiento.get_url(ente)
    if destino == "id_link_tit_mod_":
        destino = f"{destino}{titular.sk}"

    browser.ir_a_pag(url_origen + "?page=2")
    browser.pulsar(destino)
    browser.completar_form(
        nombre="titular nuevo",
        sk="tn",
        fecha_alta=fecha,
    )

    browser.assert_url(url_final + "?page=2")


def test_eliminar_titular(browser, titular, otro_titular):
    """ Cuando vamos a la página de eliminar titular y cliqueamos en confirmar,
        el titular es eliminado"""
    nombre_titular = titular.nombre
    browser.ir_a_pag(titular.get_delete_url())
    browser.pulsar('id_btn_confirm')
    browser.assert_url(reverse('home'))
    nombres_titular = [x.text.strip() for x in browser.encontrar_elementos('class_link_titular')]
    assert nombre_titular not in nombres_titular


@pytest.mark.parametrize("origen", ["/", "/diario/c/c/", "/diario/m/", "/diario/cm/c/"])
def test_eliminar_titular_redirige_a_pagina_desde_la_que_se_invoco(browser, origen, titular, cuenta, cuenta_ajena, entrada):
    if "m/" in origen:
        origen = f"{origen}{entrada.sk}"
    browser.ir_a_pag(origen)
    browser.pulsar(f"id_link_tit_elim_{titular.sk}")
    browser.pulsar("id_btn_confirm")
    browser.assert_url(origen)

@pytest.mark.parametrize("origen", [None, "titular"])
def test_eliminar_cuenta_desde_pagina_posterior_redirige_a_esa_pagina_con_el_ultimo_movimiento_seleccionado(
        browser, origen, mas_de_7_dias, titular, titular_gordo, entrada, request):
    if origen:
        ente = request.getfixturevalue(origen)
        url_origen = ente.get_absolute_url()
        dias = list(ente.dias())
    else:
        ente = None
        url_origen = reverse("home")
        dias = list(mas_de_7_dias)
    movimiento = dias[-8].movimientos.last()
    url_destino = movimiento.get_url(ente)

    browser.ir_a_pag(url_origen + "?page=2")
    browser.pulsar(f"id_link_tit_elim_{titular_gordo.sk}")
    browser.pulsar("id_btn_confirm")

    browser.assert_url(url_destino + "?page=2")
