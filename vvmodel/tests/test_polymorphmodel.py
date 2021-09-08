from django.test import TestCase

from vvmodel.tests.models import MiTestPolymorphModel, MiTestPolymorphSubmodel, \
    MiTestRelatedModel, MiTestPolymorphSubSubModel


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

    def test_es_le_misme_que_devuelve_true_para_elementos_iguales_tomados_como_clases_distintas(self):
        obj = MiTestPolymorphModel.tomar(numero=2, polymorphic=False)
        obj_sub = MiTestPolymorphSubmodel.tomar(numero=2)

        self.assertTrue(obj_sub.es_le_misme_que(obj))
        self.assertTrue(obj.es_le_misme_que(obj_sub))

    def test_es_le_misme_que_devuelve_false_para_elementos_distintos_tomados_como_clases_distintas(self):
        obj = MiTestPolymorphModel.tomar(numero=2, polymorphic=False)
        obj_sub = MiTestPolymorphSubmodel.crear(
            nombre='subobjeto distinto', numero=3, detalle='detalle')

        self.assertFalse(obj_sub.es_le_misme_que(obj))

    def test_es_le_misme_que_devuelve_false_para_elementos_distintos_tomados_como_la_misma_clase(self):
        obj_s1 = MiTestPolymorphSubmodel.tomar(numero=2, polymorphic=False)
        obj_s2 = MiTestPolymorphSubmodel.crear(
            nombre='subobjeto distinto', numero=3, detalle='detalle')

        self.assertFalse(obj_s1.es_le_misme_que(obj_s2))

    def test_es_le_misme_que_devuelve_false_si_uno_de_los_objetos_no_esta_en_la_base_de_datos(self):
        obj = MiTestPolymorphModel(nombre='objeto', numero=1)
        subobj = MiTestPolymorphSubmodel(
            nombre='subobjeto', numero=2, detalle='cosas')

        self.assertFalse(self.obj.es_le_misme_que(obj))
        self.assertFalse(obj.es_le_misme_que(self.obj))
        self.assertFalse(self.obj_sub.es_le_misme_que(subobj))
        self.assertFalse(subobj.es_le_misme_que(self.obj_sub))

    def test_es_le_misme_que_devuelve_false_si_no_son_submodelos_del_mismo_modelo(self):
        mov = MiTestRelatedModel.crear(nombre='otro modelo')
        self.assertFalse(self.obj.es_le_misme_que(mov))

    def test_primer_ancestre_devuelve_el_primer_modelo_del_que_deriva_el_de_un_objeto(self):
        subsubobj = MiTestPolymorphSubSubModel(nombre='subsub', numero=3, detalle='cosas')
        self.assertEqual(subsubobj.primer_ancestre(), MiTestPolymorphModel)

    def test_primer_ancestre_devuelve_el_propio_modelo_si_no_tiene_ancestros(self):
        obj = MiTestPolymorphModel(nombre='test', numero=3)
        self.assertEqual(obj.primer_ancestre(), MiTestPolymorphModel)

    def test_actualizar_subclase_devuelve_el_mismo_objeto_actualizado_como_subclase(self):
        obj = MiTestPolymorphSubmodel.crear(
            nombre="subobject", numero=1, detalle="detalles")
        superobj = MiTestPolymorphModel.tomar(pk=obj.pk, polymorphic=False)
        self.assertEqual(type(superobj.actualizar_subclase()), MiTestPolymorphSubmodel)
