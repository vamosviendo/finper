import datetime
from unittest.mock import patch

from django.db.models import QuerySet

from .models import MiTestModel, MiTestRelatedModel

from django.test import TestCase


class TestMiModel(TestCase):

    def setUp(self):
        super().setUp()
        self.ro = MiTestRelatedModel.objects.create(nombre='related object')
        self.o1 = MiTestModel.objects.create(
            nombre='obj1', numero=10.0, related=self.ro)
        self.o2 = MiTestModel.objects.create(
            nombre='obj2', numero=25.5, related=self.ro)


class TestMiModelMetodos(TestMiModel):

    def test_todes_devuelve_todos_los_objetos(self):
        self.assertEqual(
            list(MiTestModel.todes()),
            list(MiTestModel.objects.all())
        )

    def test_todes_devuelve_QuerySet(self):
        self.assertIsInstance(MiTestModel.todes(), QuerySet)

    def test_primere_devuelve_primer_objeto(self):
        self.assertEqual(MiTestModel.primere(), self.o1)

    def test_ultime_devuelve_ultimo_objeto(self):
        self.assertEqual(MiTestModel.ultime(), self.o2)

    def test_tomar_devuelve_objeto_indicado(self):
        self.assertEqual(MiTestModel.tomar(nombre='obj2'), self.o2)

    def test_cantidad_devuelve_cantidad_de_objetos(self):
        self.assertEqual(MiTestModel.cantidad(), 2)

    def test_excepto_devuelve_todos_los_objetos_excepto_uno(self):
        self.assertEqual(list(MiTestModel.excepto(pk=self.o1.pk)), [self.o2])

    def test_filtro_devuelve_todos_los_objetos_que_coincidan(self):
        o3 = MiTestModel.objects.create(
            nombre='obj3', numero=10.0, related=self.ro
        )
        self.assertEqual(list(MiTestModel.filtro(numero=10.0)), [self.o1, o3])


class TestMiModelCrear(TestMiModel):

    def test_crea_objeto(self):
        MiTestModel.crear(
            nombre='obj3', numero=10.0, related=self.ro
        )
        self.assertEqual(MiTestModel.cantidad(), 3)

    def test_devuelve_objeto(self):
        obj3 = MiTestModel.crear(
            nombre='obj3', numero=10.0, related=self.ro
        )
        self.assertEqual(obj3.nombre, 'obj3')
        self.assertEqual(obj3.numero, 10.0)
        self.assertEqual(obj3.related, self.ro)

    @patch('vvmodel.tests.models.MiTestModel.full_clean')
    def test_verifica_objeto(self, falso_full_clean):
        MiTestModel.crear(
            nombre='obj3', numero=10.0, related=self.ro
        )
        falso_full_clean.assert_called_once()

    @patch('vvmodel.tests.models.MiTestModel.save')
    def test_guarda_objeto(self, falso_save):
        MiTestModel.crear(
            nombre='obj3', numero=10.0, related=self.ro
        )
        falso_save.assert_called_once()


class TestMiModelUpdateFrom(TestMiModel):

    def test_actualiza_objeto_existente_a_partir_de_objeto_del_mismo_tipo(self):
        ro2 = MiTestRelatedModel.crear(nombre='ro2')
        o3 = MiTestModel(
                nombre='nuevo nombre',
                numero=567,
                fecha=datetime.date(2020, 2, 2),
                related=ro2
            )
        self.o1.update_from(o3)
        self.o1.refresh_from_db()

        self.assertEqual(self.o1.nombre, 'nuevo nombre')
        self.assertEqual(self.o1.numero, 567)
        self.assertEqual(self.o1.fecha, datetime.date(2020, 2, 2))
        self.assertEqual(self.o1.related, ro2)

    def test_no_guarda_objeto_actualizado_con_commit_false(self):
        ro2 = MiTestRelatedModel.crear(nombre='ro2')
        o3 = MiTestModel(
                nombre='nuevo nombre',
                numero=567,
                fecha=datetime.date(2020, 2, 2),
                related=ro2
            )
        self.o1.update_from(o3, commit=False)
        self.o1.refresh_from_db()
        self.assertEqual(self.o1.nombre, 'obj1')
        self.assertEqual(self.o1.numero, 10.0)
        self.assertEqual(self.o1.related, self.ro)

    def test_actualiza_objeto_aunque_no_lo_guarde_con_commit_false(self):
        ro2 = MiTestRelatedModel.crear(nombre='ro2')
        o3 = MiTestModel(
                nombre='nuevo nombre',
                numero=567,
                fecha=datetime.date(2020, 2, 2),
                related=ro2
            )
        self.o1.update_from(o3, commit=False)

        self.assertEqual(self.o1.nombre, 'nuevo nombre')
        self.assertEqual(self.o1.numero, 567)
        self.assertEqual(self.o1.fecha, datetime.date(2020, 2, 2))
        self.assertEqual(self.o1.related, ro2)

    def test_actualiza_solo_campos_pasados_como_argumento(self):
        o3 = MiTestModel(
                nombre='nuevo nombre',
            )
        self.o1.update_from(o3)
        self.o1.refresh_from_db()
        self.assertEqual(self.o1.nombre, 'nuevo nombre')
        self.assertEqual(self.o1.numero, 10.0)
        self.assertEqual(self.o1.related, self.ro)

    def test_devuelve_objeto_actualizado(self):
        ro2 = MiTestRelatedModel.crear(nombre='ro2')
        o3 = MiTestModel(
                nombre='nuevo nombre',
                numero=567,
                fecha=datetime.date(2020, 2, 2),
                related=ro2
            )
        updated_o1 = self.o1.update_from(o3, commit=False)

        self.assertEqual(updated_o1.nombre, o3.nombre)
        self.assertEqual(updated_o1.numero, o3.numero)
        self.assertEqual(updated_o1.fecha, o3.fecha)
        self.assertEqual(updated_o1.related, o3.related)


class TestGetClass(TestCase):

    def test_devuelve_la_clase_del_objeto(self):
        ro = MiTestRelatedModel.crear(nombre='ro2')
        o = MiTestModel(
                nombre='nuevo nombre',
                numero=567,
                fecha=datetime.date(2020, 2, 2),
                related=ro
            )
        self.assertEqual(ro.get_class(), MiTestRelatedModel)
        self.assertEqual(o.get_class(), MiTestModel)


class TestGetClassName(TestCase):

    def test_devuelve_una_cadena_con_el_nombre_de_la_clase_del_objeto(self):
        ro = MiTestRelatedModel.crear(nombre='ro2')
        o = MiTestModel(
                nombre='nuevo nombre',
                numero=567,
                fecha=datetime.date(2020, 2, 2),
                related=ro
            )
        clase = ro.get_class_name()
        clase2 = o.get_class_name()
        self.assertEqual(type(clase), str)
        self.assertEqual(clase, 'MiTestRelatedModel')
        self.assertEqual(clase2, 'MiTestModel')


class TestGetLowerClassName(TestCase):

    def test_devuelve_una_cadena_con_el_nombre_de_la_clase_en_minusculas(self):
        ro = MiTestRelatedModel.crear(nombre='ro2')
        clase = ro.get_lower_class_name()
        self.assertEqual(clase, ro.get_class_name().lower())


class TestTomarDeBd(TestCase):

    def test_devuelve_la_version_guardada_de_un_objeto(self):
        objeto = MiTestRelatedModel.crear(nombre='objeto guardado')
        obj_guardado = MiTestRelatedModel.tomar(nombre='objeto guardado')

        objeto.nombre = 'objeto modificado y no guardado'

        self.assertEqual(objeto.tomar_de_bd(), obj_guardado)

    def test_si_no_hay_version_guardada_de_un_objeto_devuelve_none(self):
        objeto = MiTestRelatedModel(nombre='objeto nuevo')
        self.assertIsNone(objeto.tomar_de_bd())
