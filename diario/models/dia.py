from datetime import date
from typing import Optional, Self, TYPE_CHECKING

from django.db import models
from django.db.models import Q

from vvmodel.models import MiModel

if TYPE_CHECKING:
    from diario.models import CuentaInteractiva, Movimiento


class DiaManager(models.Manager):
    def get_by_natural_key(self, fecha):
        return self.get(fecha=fecha)


class Dia (MiModel):
    fecha = models.DateField(unique=True)

    objects = DiaManager()

    class Meta:
        ordering = ['fecha']

    def __str__(self) -> str:
        return self.fecha.strftime('%Y-%m-%d')

    def de_la_semana(self):
        from utils.tiempo import dia_de_la_semana
        return dia_de_la_semana[self.fecha.weekday()]

    def str_dia_semana(self):
        return f"{self.de_la_semana()} {self.__str__()}"

    def natural_key(self) -> tuple[str]:
        return (self.fecha, )

    @property
    def identidad(self) -> str:
        return self.fecha.strftime('%Y%m%d')

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
    def ultima_fecha(cls) -> Optional[date]:
        try:
            return cls.ultime().fecha
        except AttributeError:  # No hay días
            return None

    @classmethod
    def ultima_id(cls) -> int:
        return cls.ultime().pk

    @property
    def movimientos(self) -> models.QuerySet['Movimiento']:
        return self.movimiento_set.all()

    def movimientos_filtrados(self, cuenta: 'CuentaInteractiva' = None) -> models.QuerySet['Movimiento']:
        if cuenta:
            return self.movimientos.filter(Q(cta_entrada=cuenta) | Q(cta_salida=cuenta))
        return self.movimientos

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
