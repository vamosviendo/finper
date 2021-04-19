from django.core.exceptions import ValidationError
from django.db import models


class Cuenta(models.Model):
    nombre = models.CharField(max_length=50, unique=True)


class Movimiento(models.Model):
    fecha = models.DateField()
    concepto = models.CharField(max_length=80)
    detalle = models.TextField(blank=True, null=True)
    importe = models.FloatField()
    cta_entrada = models.ForeignKey(
        Cuenta, related_name='entradas', null=True, blank=True,
        on_delete=models.CASCADE
    )
    cta_salida = models.ForeignKey(
        Cuenta, related_name='salidas', null=True, blank=True,
        on_delete=models.CASCADE
    )

    def clean(self):
        super().clean()
        if not self.cta_entrada and not self.cta_salida:
            raise ValidationError(
                message='Debe haber una cuenta de entrada, '
                        'una de salida o ambas.'
            )
        if self.cta_entrada == self.cta_salida:
            raise ValidationError(
                message='Cuentas de entrada y salida no pueden ser la misma.')