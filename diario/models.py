from django.db import models


class Cuenta(models.Model):
    nombre = models.TextField(max_length=50)