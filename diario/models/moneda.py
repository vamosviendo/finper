from typing import Self

from django.db import models

from vvmodel.models import MiModel


class Moneda(MiModel):
    monname = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)
    cotizacion = models.FloatField()

    def cotizacion_en(self, otra_moneda: Self) -> float:
        return self.cotizacion / otra_moneda.cotizacion
