from diario.models import Titular
from diario.settings_app import TITULAR_PRINCIPAL


class TestMetodoPorDefecto:

    def test_devuelve_pk_de_titular_principal(self):
        titular_principal = Titular.crear(
            titname=TITULAR_PRINCIPAL['titname'],
            nombre=TITULAR_PRINCIPAL['nombre']
        )
        assert Titular.por_defecto() == titular_principal.pk

    def test_crea_titular_principal_si_no_existe(self):
        cantidad_titulares = Titular.cantidad()
        pk_titular_principal = Titular.por_defecto()
        assert Titular.cantidad() == cantidad_titulares + 1
        assert Titular.primere() == Titular.tomar(pk=pk_titular_principal)


class TestMetodoTomarODefault:

    def test_devuelve_titular_si_existe(self, titular):
        assert Titular.tomar_o_default(titname=titular.titname) == titular

    def test_devuelve_titular_por_defecto_si_no_encuentra_titular(self, titular):
        titname = titular.titname
        titular.delete()
        assert \
            Titular.tomar_o_default(titname=titname) == \
            Titular.tomar(pk=Titular.por_defecto())
