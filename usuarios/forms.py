# from crispy_forms.helper import FormHelper
# from crispy_forms.layout import Layout, Fieldset, Field, Hidden, Submit
# from django.contrib.auth.forms import AuthenticationForm
#
#
# class LoginForm(AuthenticationForm):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         self.error_messages['invalid_login'] = \
#             'Nombre de usuario o password incorrectes'
#
#         self.helper = FormHelper()
#         self.helper.form_method = 'post'
#         self.helper.form_class = 'cf_login'
#         self.helper.form_id = 'id_form_login'
#         self.helper.layout = Layout(
#             Fieldset(
#                 'Login',
#                 Field('username', autocomplete='off'),
#                 Field('password'),
#             ),
#             Hidden('next', '{{ next }}'),
#             Submit(
#                 'entrar',
#                 'Entrar',
#                 css_class='btn btn-primary',
#                 css_id='id_btn_login',
#             ),
#         )
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autocomplete': 'off'})
        self.error_messages['invalid_login'] = \
            'Nombre de usuario o password incorrectes'
