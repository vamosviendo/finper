from __future__ import annotations

from typing import Self

from django.db import models

from diario.settings_app import MONEDA_BASE
from vvmodel.models import MiModel


class MonedaManager(models.Manager):
    def get_by_natural_key(self, monname):
        return self.get(monname=monname)


class Moneda(MiModel):
    monname = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    _plural = models.CharField(max_length=100, null=True, blank=True)
    cotizacion = models.FloatField()

    objects = MonedaManager()

    def __str__(self):
        return self.nombre

    def natural_key(self) -> tuple[str]:
        return (self.monname, )

    @property
    def plural(self) -> str:
        if self._plural:
            return self._plural
        return f'{self.nombre.lower()}s'

    @plural.setter
    def plural(self, value: str):
        self._plural = value.lower()

    @classmethod
    def base(cls):
        return cls.tomar(monname=MONEDA_BASE)

    def cotizacion_en(self, otra_moneda: Self) -> float:
        return self.cotizacion / otra_moneda.cotizacion

    def as_view_context(self) -> dict[str, str | float]:
        return {
            'monname': self.monname,
            'nombre': self.nombre,
            'cotizacion': self.cotizacion,
        }
