from datetime import date

from django.core.exceptions import ValidationError
from django.db import models


class Movimiento(models.Model):
    fecha = models.DateField()
    concepto = models.CharField(max_length=30)
    detalle = models.CharField(max_length=30, null=True, blank=True)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    cta_entrada = models.CharField(max_length=15, null=True, blank=True)
    cta_salida = models.CharField(max_length=15, null=True, blank=True)

    def clean(self):
        super().clean()
        if self.cta_entrada is None and self.cta_salida is None:
            raise ValidationError('Entrada y salida no pueden ser ambos nulos')

    @classmethod
    def crear(cls, concepto='', fecha=date.today(),
              detalle='', importe=0, cta_entrada=None, cta_salida=None):
        mov = cls(concepto=concepto, fecha=fecha, detalle=detalle,
                  importe=importe, cta_entrada=cta_entrada,
                  cta_salida=cta_salida)
        mov.full_clean()
        mov.save()
        return mov
