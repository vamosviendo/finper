from django.core.exceptions import ValidationError
from django.db import models
from django.utils.datetime_safe import date

from utils import errors


def hoy():
    return date.today()


class Cuenta(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    slug = models.CharField(max_length=4, unique=True)
    saldo = models.FloatField(default=0)

    @staticmethod
    def crear(nombre, slug):
        cuenta = Cuenta(nombre=nombre, slug=slug)
        cuenta.full_clean()
        cuenta.save()
        return cuenta

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.slug = self.slug.upper()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.saldo != 0:
            raise ValueError
        super().delete(*args, **kwargs)


class Movimiento(models.Model):
    fecha = models.DateField(default=hoy)
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
            raise ValidationError(message=errors.CUENTA_INEXISTENTE)
        if self.cta_entrada == self.cta_salida:
            raise ValidationError(message=errors.CUENTAS_IGUALES)

    def delete(self, *args, **kwargs):
        if self.cta_entrada:
            self.cta_entrada.saldo -= self.importe
            self.cta_entrada.save()
        if self.cta_salida:
            self.cta_salida.saldo += self.importe
            self.cta_salida.save()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.cta_entrada:
                self.cta_entrada.saldo += self.importe
                self.cta_entrada.save()
            if self.cta_salida:
                self.cta_salida.saldo -= self.importe
                self.cta_salida.save()

        super().save(*args, **kwargs)