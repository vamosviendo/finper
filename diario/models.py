from django.core.exceptions import ValidationError
from django.db import models


class Cuenta(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    saldo = models.FloatField(default=0)

    def __str__(self):
        return self.nombre


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

    def __str__(self):
        string = f'{self.fecha.strftime("%Y-%m-%d")} {self.concepto}: ' \
                 f'{self.importe}'
        if self.cta_entrada:
            string += f' +{self.cta_entrada}'
        if self.cta_salida:
            string += f' -{self.cta_salida}'
        return string

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

    def save(self, *args, **kwargs):
        if self.cta_entrada:
            self.cta_entrada.saldo += self.importe
            self.cta_entrada.save()
        if self.cta_salida:
            self.cta_salida.saldo -= self.importe
            self.cta_salida.save()
        super().save(*args, **kwargs)