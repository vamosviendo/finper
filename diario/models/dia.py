from django.db import models

from vvmodel.models import MiModel


class Dia (MiModel):
    fecha = models.DateField(unique=True)

    class Meta:
        ordering = ['fecha']
