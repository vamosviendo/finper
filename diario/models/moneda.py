from __future__ import annotations

from datetime import date
from typing import Self, TYPE_CHECKING

from django.core.exceptions import EmptyResultSet
from django.db import models
from django.urls import reverse

from diario.models import Cotizacion
from diario.models.dia import Dia
from diario.settings_app import MONEDA_BASE
from vvmodel.models import MiModel

if TYPE_CHECKING:
    from diario.models.cuenta import CuentaManager, Cuenta
    from diario.models.movimiento import MovimientoManager, Movimiento


class MonedaManager(models.Manager):
    def get_by_natural_key(self, sk):
        return self.get(sk=sk)


class Moneda(MiModel):
    sk = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    _plural = models.CharField(max_length=100, null=True, blank=True)

    cotizaciones: models.Manager["Cotizacion"]      # related name para Cotizacion.moneda
    cuenta_set: CuentaManager                       # related name para Cuenta.moneda
    movimientos: MovimientoManager                  # related name para Movimiento.moneda

    objects = MonedaManager()
    form_fields = ('nombre', 'sk', 'plural', )

    def __str__(self) -> str:
        return self.nombre

    def get_absolute_url(self) -> str:
        return reverse("moneda", args=[self.sk])

    def get_edit_url(self) -> str:
        return reverse("mon_mod", args=[self.sk])

    def get_delete_url(self) -> str:
        return reverse("mon_elim", args=[self.sk])

    def get_cot_nueva(self) -> str:
        return reverse("mon_cot_nueva", args=[self.sk])

    def natural_key(self) -> tuple[str]:
        return (self.sk, )

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
            ultimo_dia = Dia.ultime()
            fecha = ultimo_dia.fecha if ultimo_dia else date.today()
            self._cotizacion = Cotizacion(fecha=fecha, importe_compra=value)

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
            ultimo_dia = Dia.ultime()
            fecha = ultimo_dia.fecha if ultimo_dia else date.today()
            self._cotizacion = Cotizacion(fecha=fecha, importe_venta=value)

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
        return cls.tomar(sk=MONEDA_BASE)

    def cotizacion_al(self, fecha: date, compra: bool) -> float:
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
