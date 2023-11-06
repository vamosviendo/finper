from django.db import models

from vvmodel.models import MiModel


class Moneda(MiModel):
    monname = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)
    cotizacion = models.FloatField()
