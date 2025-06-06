from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Self, TYPE_CHECKING

from django.db import models
from django.db.models import Count, QuerySet

from vvmodel.models import MiModel

if TYPE_CHECKING:
    from diario.models import Cuenta, Movimiento, Titular
    from diario.models.movimiento import MovimientoManager


class DiaManager(models.Manager):
    def get_by_natural_key(self, fecha):
        return self.get(fecha=fecha)


class Dia (MiModel):
    fecha = models.DateField(unique=True)

    movimiento_set: MovimientoManager["Movimiento"]  # related name para Movimiento.dia

    objects = DiaManager()

    class Meta:
        ordering = ['fecha']

    def __str__(self) -> str:
        return self.fecha.strftime('%Y-%m-%d')

    def __gt__(self, otro: Self) -> bool:
        return self.fecha > otro.fecha

    def de_la_semana(self):
        from utils.tiempo import dia_de_la_semana
        return dia_de_la_semana[self.fecha.weekday()]

    def str_dia_semana(self):
        return f"{self.de_la_semana()} {self.__str__()}"

    def natural_key(self) -> tuple[str]:
        return (self.fecha, )

    @property
    def sk(self) -> str:
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

    @classmethod
    def con_movimientos(cls, cuenta: Cuenta | None = None) -> QuerySet[Self]:
        if cuenta:
            return cuenta.dias()
        dias = Dia.objects.annotate(mov_count=Count('movimiento_set'))
        return dias.filter(mov_count__gt=0).order_by('fecha')

    @property
    def movimientos(self) -> models.QuerySet['Movimiento']:
        return self.movimiento_set.all()

    def timedelta(self, cantidad: int) -> Self:
        try:
            return Dia.tomar(fecha=self.fecha+timedelta(cantidad))
        except Dia.DoesNotExist:
            return Dia.crear(fecha=self.fecha+timedelta(cantidad))

    def movimientos_filtrados(
            self, ente: Cuenta | Titular | None = None) -> models.QuerySet['Movimiento']:
        if ente:
            return ente.movs().filter(dia=self)
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
