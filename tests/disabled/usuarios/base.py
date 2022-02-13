from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UsuarioUnitTest(TestCase):
    """ Superclase para diario de la app usuarios."""

    def setUp(self):
        # Generar usuario de prueba
        user = User.objects.create_user(
            username='lilitest',
            password='passwordtest'
        )
