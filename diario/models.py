from datetime import date

from django.core.exceptions import ValidationError
from django.db import models


class Movimiento(models.Model):
    fecha = models.DateField()
    concepto = models.CharField(max_length=30)
    detalle = models.CharField(max_length=30, null=True, blank=True)
    entrada = models.DecimalField(max_digits=12, decimal_places=2,
                                  null=True, blank=True)
    salida = models.DecimalField(max_digits=12, decimal_places=2,
                                 null=True, blank=True)

    def clean(self):
        super().clean()
        if self.entrada is None and self.salida is None:
            raise ValidationError('Entrada y salida no pueden ser ambos nulos')

    @classmethod
    def crear(cls, concepto='', fecha=date.today(),
              detalle='', entrada=None, salida=None):
        mov = cls(concepto=concepto, fecha=fecha, detalle=detalle,
                  entrada=entrada, salida=salida)
        mov.full_clean()
        mov.save()
        return mov
