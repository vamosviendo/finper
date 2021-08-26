from django.test import TestCase

from vvmodel.tests.models import MiTestPolymorphModel, MiTestPolymorphSubmodel


class PolymorphModelMetodos(TestCase):

    def setUp(self):
        self.obj = MiTestPolymorphModel.crear(nombre='objeto', numero=1)
        self.obj_sub = MiTestPolymorphSubmodel.crear(
            nombre='subobjeto', numero=2, detalle='cosas')

    def test_tomar_devuelve_objeto_polimorfico(self):
        self.assertEqual(
            MiTestPolymorphModel.tomar(numero=2).get_class(),
            MiTestPolymorphSubmodel
        )
        self.assertNotEqual(
            MiTestPolymorphModel.tomar(numero=2).get_class(),
            MiTestPolymorphModel
        )

    def test_tomar_devuelve_objeto_no_polimorfico_con_polymorphic_false(self):
        self.assertEqual(
            MiTestPolymorphModel.tomar(numero=2, polymorphic=False).get_class(),
            MiTestPolymorphModel
        )
        self.assertNotEqual(
            MiTestPolymorphModel.tomar(numero=2, polymorphic=False).get_class(),
            MiTestPolymorphSubmodel
        )

    def test_como_subclase_devuelve_objeto_como_instancia_del_submodelo(self):
        obj = MiTestPolymorphModel.tomar(numero=2, polymorphic=False)
        self.assertEqual(
            obj.como_subclase().get_class(),
            MiTestPolymorphSubmodel
        )
        self.assertNotEqual(
            obj.como_subclase().get_class(),
            MiTestPolymorphModel
        )

    def test_save_guarda_app_en_campo_content_type(self):
        obj = MiTestPolymorphModel(nombre='objeto polimórfico', numero=3)
        obj.save()
        self.assertEqual(obj.content_type.app_label, 'vvmodel')

    def test_save_guarda_modelo_en_campo_content_type(self):
        obj = MiTestPolymorphModel(nombre='objeto polimórfico', numero=3)
        objsub = MiTestPolymorphSubmodel(
            nombre='subobjeto polimórfico', numero=4)

        obj.save()
        self.assertEqual(obj.content_type.model, 'mitestpolymorphmodel')

        objsub.save()
        self.assertEqual(
            objsub.content_type.model, 'mitestpolymorphsubmodel')
