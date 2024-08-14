from __future__ import annotations

from datetime import date
from typing import Self

from django.core.exceptions import ValidationError
from django.db import models

from diario.models import Cotizacion
from diario.settings_app import MONEDA_BASE
from vvmodel.models import MiModel


class MonedaManager(models.Manager):
    def get_by_natural_key(self, monname):
        return self.get(monname=monname)


class Moneda(MiModel):
    monname = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    _plural = models.CharField(max_length=100, null=True, blank=True)

    objects = MonedaManager()

    def __str__(self):
        return self.nombre

    def natural_key(self) -> tuple[str]:
        return (self.monname, )

    @property
    def cotizacion(self) -> float:
        try:
            return self.cotizaciones.last().importe
        except AttributeError:
            return 1

    @cotizacion.setter
    def cotizacion(self, value: float):
        """ Si no existe una cotización para la fecha, la crea.
            Si existe, actualiza el importe. """
        self._cotizacion = Cotizacion(fecha=date.today(), importe=value)

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

    def cotizacion_al(self, fecha: date) -> float:
        return Cotizacion.tomar(moneda=self, fecha=fecha).importe

    def cotizacion_en(self, otra_moneda: Self) -> float:
        return self.cotizacion / otra_moneda.cotizacion

    def cotizacion_en_al(self, otra_moneda: Self, fecha: date) -> float:
        return self.cotizacion_al(fecha) / otra_moneda.cotizacion_al(fecha)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if hasattr(self, "_cotizacion"):
            _cotizacion = getattr(self, "_cotizacion")
            moneda = self.tomar_de_bd()
            try:
                Cotizacion.crear(moneda=moneda, fecha=_cotizacion.fecha, importe=_cotizacion.importe)
            except ValidationError:
                cot = Cotizacion.tomar(moneda=moneda, fecha=_cotizacion.fecha)
                cot.importe = _cotizacion.importe
                cot.save()


    def as_view_context(self) -> dict[str, str | float]:
        return {
            'monname': self.monname,
            'nombre': self.nombre,
            'cotizacion': self.cotizacion,
        }
