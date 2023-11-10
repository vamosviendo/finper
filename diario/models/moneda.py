from __future__ import annotations

from typing import Self

from django.db import models

from vvmodel.models import MiModel


class Moneda(MiModel):
    monname = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    cotizacion = models.FloatField()

    def __str__(self):
        return self.nombre

    def cotizacion_en(self, otra_moneda: Self) -> float:
        return self.cotizacion / otra_moneda.cotizacion

    def as_view_context(self) -> dict[str, str | float]:
        return {
            'monname': self.monname,
            'nombre': self.nombre,
            'cotizacion': self.cotizacion,
        }
