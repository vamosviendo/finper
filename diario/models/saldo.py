from django.core.exceptions import ValidationError
from django.db import models

from vvmodel.models import MiModel


class Saldo(MiModel):

    cuenta = models.ForeignKey('diario.Cuenta', on_delete=models.CASCADE)
    fecha = models.DateField()
    importe = models.FloatField()

    class Meta:
        unique_together = ['cuenta', 'fecha']
        ordering = ['fecha', 'cuenta']

    @classmethod
    def tomar(cls, **kwargs):
        try:
            return super().tomar(**kwargs)
        except cls.DoesNotExist:
            result = Saldo.filtro(
                cuenta=kwargs['cuenta'],
                fecha__lt=kwargs['fecha']
            ).last()

            if result is None:
                raise cls.DoesNotExist

            return result

    @classmethod
    def registrar(cls, cuenta, fecha, importe):
        if len(cls.filtro(cuenta=cuenta, fecha=fecha)) == 0:
            cls.crear(cuenta=cuenta, fecha=fecha, importe=importe)

