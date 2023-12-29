from datetime import date
from typing import Self

from django.db import models

from vvmodel.models import MiModel


class Dia (MiModel):
    fecha = models.DateField(unique=True)

    class Meta:
        ordering = ['fecha']

    @classmethod
    def hoy(cls) -> Self:
        try:
            return cls.tomar(fecha=date.today().strftime('%Y%m%d'))
        except Dia.DoesNotExist:
            return cls.crear(fecha=date.today())
