from django.contrib import auth
from django.urls import reverse

from vvutils.os import env_or_input
from usuarios.forms import LoginForm
from .base import UsuarioUnitTest

TEST_USERNAME = env_or_input('TEST_USERNAME')
TEST_PASSWORD = env_or_input('TEST_PASSWORD')


class TestLogin(UsuarioUnitTest):

    def postear(self, username, password, url='/'):
        """ Hace un request de tipo POST a login con el nombre de usuario y
            password proporcionados, y se dirige a la url dada."""
        response = self.client.post(
            reverse('login'),
            data={
                'username': username,
                'password': password,
                'next': url,
            }
        )
        return response

    def test_usa_template_login(self):
        response = self.client.get(reverse('login'))
        self.assertTemplateUsed(response, 'usuarios/login.html')

    def test_usa_form_LoginForm(self):
        response = self.client.get(reverse('login'))
        self.assertIsInstance(response.context['form'], LoginForm)

    def test_comprueba_usuario_y_password(self):
        self.postear(TEST_USERNAME, TEST_PASSWORD)
        self.assertTrue(auth.get_user(self.client).is_authenticated)

    def test_no_admite_usuario_inexistente(self):
        self.postear('usuarioincorrecto', TEST_PASSWORD)
        self.assertFalse(auth.get_user(self.client).is_authenticated)

    def test_no_admite_password_incorrecta(self):
        self.postear(TEST_USERNAME, 'passwordincorrecta')
        self.assertFalse(auth.get_user(self.client).is_authenticated)

    def test_redirige_a_login_despues_de_rechazar_usuario(self):
        response = self.postear('usuariono', 'passwordno')
        self.assertTemplateUsed(response, 'usuarios/login.html')

    def test_pasa_mensajes_de_error(self):
        response = self.postear('usuariono', 'passwordno')
        errors = response.context['form'].error_messages
        self.assertIn('invalid_login', errors.keys())
        self.assertIn(
            'Nombre de usuario o password incorrectes',
            errors['invalid_login']
        )


class TestLogout(UsuarioUnitTest):

    def test_redirige_a_home(self):
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, '/')

    def test_cierra_sesion_usuario(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        self.client.get(reverse('logout'))
        self.assertFalse(auth.get_user(self.client).is_authenticated)
