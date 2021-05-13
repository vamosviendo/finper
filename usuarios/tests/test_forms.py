from usuarios.forms import LoginForm
from .base import UsuarioUnitTest


class LoginFormTest(UsuarioUnitTest):

    def test_pasa_mensaje_de_error_de_login(self):
        """ Ante un login incorrecto, pasa mensaje de error al form."""
        f = LoginForm(data={'username': 'lilino', 'password': 'passwdno'})
        self.assertFalse(f.is_valid())
        self.assertIn('invalid_login', f.error_messages.keys())
        self.assertIn(
            'Nombre de usuario o password incorrectes',
            f.error_messages['invalid_login']
        )
