from __future__ import annotations

from datetime import date
from typing import Self

from django.core.exceptions import EmptyResultSet
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
    def cotizacion_compra(self) -> float:
        try:
            return self._cotizacion.importe_compra
        except AttributeError:
            try:
                return self.cotizaciones.last().importe_compra
            except (ValueError, AttributeError):
                return 1

    @cotizacion_compra.setter
    def cotizacion_compra(self, value: float):
        """ Si no existe una cotización para la fecha, la crea.
            Si existe, actualiza el importe. """
        try:
            self._cotizacion.importe_compra = value
        except AttributeError:
            self._cotizacion = Cotizacion(fecha=date.today(), importe_compra=value)

    @property
    def cotizacion_venta(self) -> float:
        try:
            return self._cotizacion.importe_venta
        except AttributeError:
            try:
                return self.cotizaciones.last().importe_venta
            except (ValueError, AttributeError):
                return 1

    @cotizacion_venta.setter
    def cotizacion_venta(self, value: float):
        """ Si no existe una cotización para la fecha, la crea.
            Si existe, actualiza el importe. """
        try:
            self._cotizacion.importe_venta = value
        except AttributeError:
            self._cotizacion = Cotizacion(fecha=date.today(), importe_venta=value)

    @property
    def cotizacion(self) -> float:
        return self.cotizacion_venta

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

    def cotizacion_al(self, fecha: date, compra: bool):
        cotizacion = Cotizacion.tomar(moneda=self, fecha=fecha)
        return cotizacion.importe_compra if compra else cotizacion.importe_venta

    def cotizacion_compra_al(self, fecha: date) -> float:
        return self.cotizacion_al(fecha, compra=True)

    def cotizacion_venta_al(self, fecha: date) -> float:
        return self.cotizacion_al(fecha, compra=False)

    def cotizacion_en(self, otra_moneda: Self, compra: bool) -> float:
        if otra_moneda == self:
            return 1
        return \
            (self.cotizacion_compra / otra_moneda.cotizacion_venta) if compra else \
            (self.cotizacion_venta / otra_moneda.cotizacion_compra)

    def cotizacion_compra_en(self, otra_moneda: Self) -> float:
        return self.cotizacion_en(otra_moneda, compra=True)

    def cotizacion_venta_en(self, otra_moneda: Self) -> float:
        return self.cotizacion_en(otra_moneda, compra=False)

    def cotizacion_en_al(self, otra_moneda: Self, fecha: date, compra: bool) -> float:
        if otra_moneda == self:
            return 1
        return self.cotizacion_al(fecha, compra=compra) / otra_moneda.cotizacion_al(fecha, compra=not compra)

    def cotizacion_compra_en_al(self, otra_moneda: Self, fecha: date) -> float:
        return self.cotizacion_en_al(otra_moneda, fecha, compra=True)

    def cotizacion_venta_en_al(self, otra_moneda: Self, fecha: date) -> float:
        return self.cotizacion_en_al(otra_moneda, fecha, compra=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if hasattr(self, "_cotizacion"):
            _cotizacion = getattr(self, "_cotizacion")
            moneda = self.tomar_de_bd()
            try:
                cot = Cotizacion.tomar(moneda=moneda, fecha=_cotizacion.fecha)
                cot.importe_compra = _cotizacion.importe_compra
                cot.importe_venta = _cotizacion.importe_venta
                cot.save()
            except EmptyResultSet:
                Cotizacion.crear(
                    moneda=moneda,
                    fecha=_cotizacion.fecha,
                    importe_compra=_cotizacion.importe_compra,
                    importe_venta=_cotizacion.importe_venta,
                )

    def as_view_context(self) -> dict[str, str | float]:
        return {
            'monname': self.monname,
            'nombre': self.nombre,
            'cotizacion': self.cotizacion_venta,
        }
