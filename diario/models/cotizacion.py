from django.db import models

from vvmodel.models import MiModel


class Cotizacion(MiModel):
    importe = models.FloatField()
    fecha = models.DateField()
    moneda = models.ForeignKey("diario.Moneda", related_name="cotizaciones", on_delete=models.CASCADE)

    class Meta:
        ordering = ("fecha", )
        unique_together = ("fecha", "moneda", )
