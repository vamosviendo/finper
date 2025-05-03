from django.db import models

from diario.models import Movimiento
from vvmodel.models import MiModel

class SaldoDiario(MiModel):
    cuenta = models.ForeignKey('diario.Cuenta', on_delete=models.CASCADE)
    dia = models.ForeignKey(
        'diario.Dia', on_delete=models.CASCADE)
    _importe = models.FloatField()

    class Meta:
        unique_together = ['cuenta', 'dia']
        ordering = ['dia']

    @property
    def importe(self) -> float:
        return self._importe

    @importe.setter
    def importe(self, value: float):
        self._importe = round(value, 2)
