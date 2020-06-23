from django.db import models


class Movimiento(models.Model):
    fecha = models.DateField()
    concepto = models.TextField()
    detalle = models.TextField()
    entrada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    salida = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
