import pytest
from django.urls import reverse
from pytest_django import asserts

from diario.forms import FormCuenta


def test_usa_template_cta_form(client, cuenta):
    response = client.get(reverse('cta_mod', args=[cuenta.sk]))
    asserts.assertTemplateUsed(response, 'diario/cta_form.html')


def test_usa_form_cuenta(client, cuenta):
    response = client.get(
        reverse('cta_mod', args=[cuenta.sk]),
        data={'nombre': 'Nombro', 'sk': 'Slag'}
    )
    assert isinstance(response.context['form'], FormCuenta)


def test_no_permite_modificar_titular(client, cuenta, otro_titular):
    response = client.get(reverse('cta_mod', args=[cuenta.sk]))
    assert response.context['form'].fields['titular'].disabled


@pytest.mark.parametrize('cta', ['cuenta', 'cuenta_acumulativa'])
def test_post_guarda_cambios_en_cuenta_interactiva_o_acumulativa(client, cta, fecha_temprana, request):
    cuenta = request.getfixturevalue(cta)
    client.post(
        reverse('cta_mod', args=[cuenta.sk]),
        data={'nombre': 'Cuento', 'sk': 'Slag', 'fecha_creacion': fecha_temprana}
    )
    cuenta.refresh_from_db()
    assert cuenta.nombre == 'cuento'
    assert cuenta.sk == 'slag'
