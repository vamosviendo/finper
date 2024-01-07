from datetime import date
from typing import Self, TYPE_CHECKING

from django.db import models

from vvmodel.models import MiModel

if TYPE_CHECKING:
    from diario.models import Movimiento


class Dia (MiModel):
    fecha = models.DateField(unique=True)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return self.fecha.strftime('%Y-%m-%d')

    @classmethod
    def hoy(cls) -> Self:
        try:
            return cls.tomar(fecha=date.today().strftime('%Y%m%d'))
        except Dia.DoesNotExist:
            return cls.crear(fecha=date.today())

    @classmethod
    def hoy_id(cls) -> int:
        return cls.hoy().pk

    @classmethod
    def ultima_fecha(cls) -> date:
        return cls.ultime().fecha

    @property
    def movimientos(self) -> models.QuerySet['Movimiento']:
        return self.movimiento_set.all()

    def saldo(self) -> float:
        from diario.utils.utils_saldo import saldo_general_historico
        ult_mov = self.movimientos.last()

        if ult_mov is not None:
            return saldo_general_historico(ult_mov)

        try:
            return self.anterior().saldo()
        except AttributeError:  # self.anterior() == None
            return 0

    def anterior(self) -> Self:
        return self.__class__.filtro(fecha__lt=self.fecha).last()
