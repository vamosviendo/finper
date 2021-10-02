from django.db import models

from vvmodel.models import MiModel


class Titular(MiModel):
    nombre = models.CharField(max_length=100)