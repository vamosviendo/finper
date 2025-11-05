import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By


@pytest.fixture(autouse=True)
def mock_titular_principal(mocker, titular):
    return mocker.patch('diario.forms.TITULAR_PRINCIPAL', titular.sk)


def test_crear_cuenta(browser, titular, fecha):
    """ Cuando vamos a la página de cuenta nueva y completamos el formulario,
        aparece una cuenta nueva entre las cuentas del sitio. """
    browser.ir_a_pag(reverse("cta_nueva"))
    browser.completar_form(
        nombre="cuenta nueva",
        sk="cn",
        titular=titular.nombre,
        fecha_creacion=fecha,
    )

    browser.assert_url(reverse("home"))

    # Vemos que la cuenta creada aparece entre las cuentas de la página de
    # inicio
    links_cuenta = browser.encontrar_elementos("class_link_cuenta")
    nombres_cuenta = [x.text.strip() for x in links_cuenta]
    assert "cuenta nueva" in nombres_cuenta


@pytest.mark.parametrize("origen", ["/", "/diario/t/titular/", "/diario/m/", "/diario/tm/titular/"])
@pytest.mark.parametrize("destino", ["id_link_cuenta_nueva", "id_link_cta_mod_"])
def test_crear_o_modificar_cuenta_redirige_a_pagina_desde_donde_se_invoco(
        browser, origen, destino, titular, cuenta, fecha, entrada, entrada_anterior):
    if "m/" in origen:
        origen = f"{origen}{entrada_anterior.sk}"
    if destino == "id_link_cta_mod_":
        destino = f"{destino}{cuenta.sk}"
    browser.ir_a_pag(origen)
    browser.pulsar(destino)
    browser.completar_form(
        nombre="cuenta nueva",
        sk="cn",
        titular=titular.nombre,
        fecha_creacion=fecha,
    )
    browser.assert_url(origen)


@pytest.mark.parametrize("origen", [None, "titular"])
@pytest.mark.parametrize("destino", ["id_link_cuenta_nueva", "id_link_cta_mod_"])
def test_crear_o_modificar_cuenta_desde_pagina_posterior_redirige_a_esa_pagina_con_el_ultimo_movimiento_seleccionado(
        browser, cuenta, titular, fecha, mas_de_7_dias, origen, destino, request):
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
    if destino == "id_link_cta_mod_":
        destino = f"{destino}{cuenta.sk}"

    browser.ir_a_pag(url_origen + "?page=2")
    browser.pulsar(destino)
    browser.completar_form(
        nombre="cuenta nueva",
        sk="cn",
        titular=titular.nombre,
        fecha_creacion=fecha,
    )

    browser.assert_url(url_final + "?page=2")


def test_crear_cuenta_en_otra_moneda(browser, titular, fecha, dolar):
    browser.ir_a_pag(reverse("cta_nueva"))
    browser.completar_form(
        nombre="cuenta en dólares",
        sk="cd",
        titular=titular.nombre,
        fecha_creacion=fecha,
        moneda=dolar.nombre,
    )
    # Vemos que la cuenta creada tiene resaltado como saldo principal el saldo
    # en dólares
    saldo_cuenta = browser.encontrar_elemento("id_row_cta_cd").encontrar_elemento("mon_cuenta", By.CLASS_NAME)
    assert saldo_cuenta.get_attribute("id") == f"id_saldo_cta_cd_{dolar.sk}"


def test_modificar_cuenta(browser, cuenta_ajena, dolar, fecha_anterior):
    """ Cuando vamos a la página de modificar cuenta y completamos el
        formulario, la cuenta se modifica"""
    browser.ir_a_pag(cuenta_ajena.get_edit_url())
    # En todos los campos del formulario aparece el valor del campo correspondiente de la cuenta:
    browser.controlar_modelform(instance=cuenta_ajena)

    browser.completar_form(
        nombre="cuenta con nombre modificado",
        sk="ccnm",
    )
    browser.assert_url(reverse("home"))
    nombre_cuenta = browser.encontrar_elemento("id_link_cta_ccnm").text.strip()
    assert nombre_cuenta == "cuenta con nombre modificado"


def test_eliminar_cuenta(browser, cuenta, cuenta_2):
    """ Cuando vamos a la página de eliminar cuenta y cliqueamos en confirmar,
        la cuenta es eliminada"""
    nombre_cuenta = cuenta.nombre
    browser.ir_a_pag(cuenta.get_delete_url())
    browser.pulsar('id_btn_confirm')
    browser.assert_url(reverse('home'))
    nombres_cuenta = [x.text.strip() for x in browser.encontrar_elementos('class_link_cuenta')]
    assert nombre_cuenta not in nombres_cuenta


@pytest.mark.parametrize("origen", ["/", "/diario/t/titular/", "/diario/m/", "/diario/tm/titular/"])
def test_eliminar_cuenta_redirige_a_pagina_desde_la_que_se_invoco(browser, origen, cuenta, cuenta_2, entrada):
    if "m/" in origen:
        origen = f"{origen}{entrada.sk}"
    browser.ir_a_pag(origen)
    browser.pulsar(f"id_link_cta_elim_{cuenta_2.sk}")
    browser.pulsar("id_btn_confirm")
    browser.assert_url(origen)

@pytest.mark.parametrize("origen", [None, "titular"])
def test_eliminar_cuenta_desde_pagina_posterior_redirige_a_esa_pagina_con_el_ultimo_movimiento_seleccionado(
        browser, origen, mas_de_7_dias, cuenta, cuenta_3, entrada, request):
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
    browser.pulsar(f"id_link_cta_elim_{cuenta_3.sk}")
    browser.pulsar("id_btn_confirm")

    browser.assert_url(url_destino + "?page=2")
