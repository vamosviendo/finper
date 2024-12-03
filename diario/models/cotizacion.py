from datetime import date

from django.core.exceptions import EmptyResultSet
from django.db import models

from vvmodel.models import MiModel


class Cotizacion(MiModel):
    importe_compra = models.FloatField()
    importe_venta = models.FloatField()
    fecha = models.DateField()
    moneda = models.ForeignKey("diario.Moneda", related_name="cotizaciones", on_delete=models.CASCADE)

    class Meta:
        ordering = ("fecha", )
        unique_together = ("fecha", "moneda", )

    def __str__(self):
        return f"Cotización {self.moneda} al {self.fecha}: {self.importe_compra} / {self.importe_venta}"

    @classmethod
    def tomar(cls, **kwargs):
        kwargs["fecha"] = kwargs.get("fecha") or date.today()

        if "moneda" not in kwargs.keys():
            raise TypeError('Argumento "moneda" faltante')
        for key in kwargs.keys():
            if key not in ("moneda", "fecha"):
                raise TypeError(f'Argumento "{key}" inesperado')

        try:
            return super().tomar(**kwargs)
        except cls.DoesNotExist:
            cotizaciones_anteriores = cls.filtro(moneda=kwargs["moneda"], fecha__lt=kwargs["fecha"])
            if cotizaciones_anteriores.count() == 0:
                raise EmptyResultSet(
                    f"No hay cotizaciones de {kwargs['moneda']} anteriores al {kwargs['fecha']}"
                )
            return cotizaciones_anteriores.last()
