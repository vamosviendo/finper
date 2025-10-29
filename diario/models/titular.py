from __future__ import annotations

from typing import TYPE_CHECKING, Self, Optional, cast

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet, Q
from django.urls import reverse
from django.utils import timezone

from utils import errors
from vvmodel.models import MiModel
from vvutils.text import mi_slugify

from diario.models.dia import Dia

if TYPE_CHECKING:
    from diario.models import Cuenta, CuentaInteractiva, Movimiento, Moneda
    from diario.models.cuenta import CuentaManager


class TitularManager(models.Manager):
    def get_by_natural_key(self, sk):
        return self.get(_sk=sk)

class Titular(MiModel):
    sk = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100, blank=True)
    fecha_alta = models.DateField(default=timezone.now)
    deudores = models.ManyToManyField('Titular', related_name='acreedores')

    acreedores: TitularManager  # related name para campo deudores
    cuentas: CuentaManager      # related name para CuentaInteractiva.titular
    ex_cuentas: CuentaManager   # related name para CuentaAcumulativa.titular_original

    objects = TitularManager()
    form_fields = ('sk', 'nombre', 'fecha_alta', )

    def get_absolute_url(self) -> str:
        return reverse("titular", args=[self.sk])

    def get_edit_url(self) -> str:
        return reverse("tit_mod", args=[self.sk])

    def get_delete_url(self) -> str:
        return reverse("tit_elim", args=[self.sk])

    def get_url_with_mov(self, mov: Movimiento) -> str:
        return reverse("titular_movimiento", args=[self.sk, mov.sk])

    def natural_key(self) -> tuple[str]:
        return (self.sk, )

    def capital(
            self,
            movimiento: Optional['Movimiento'] = None,
            dia: Optional[Dia] = None,
            moneda: Optional[Moneda] = None,
            compra: bool = False) -> float:
        if movimiento:
            result = sum(
                c.saldo(movimiento=movimiento, moneda=moneda, compra=compra)
                for c in self.cuentas_interactivas()
            )
        elif dia:
            result = sum(c.saldo(dia=dia, moneda=moneda, compra=compra) for c in self.cuentas_interactivas())
        else:
            result = sum(c.saldo(moneda=moneda, compra=compra) for c in self.cuentas_interactivas())

        return round(result, 2)

    def saldo(
            self,
            movimiento: Movimiento = None,
            dia: Dia = None,
            moneda: Moneda = None,
            compra: bool = False) -> float:
        """ Wrapper de self.capital """
        return self.capital(movimiento, dia, moneda, compra)

    def cuentas_interactivas(self) -> models.QuerySet['CuentaInteractiva']:
        ids = [c.id for c in self.cuentas.all() if c.es_interactiva]
        return self.cuentas.filter(id__in=ids)

    def cuentas_en_las_que_participa(self) -> list['Cuenta']:
        from diario.models import Cuenta, CuentaAcumulativa
        cuentas = []
        for cuenta in Cuenta.todes():
            if cuenta in self.cuentas.all() or (
                    cuenta.es_acumulativa and self in cast(CuentaAcumulativa, cuenta).titulares
            ):
                cuentas.append(cuenta)
        return cuentas

    def dias(self) -> models.QuerySet['Dia']:
        fechas = [mov.dia.fecha for mov in self.movs()]
        return Dia.filtro(fecha__in=fechas)

    def movs(self) -> QuerySet['Movimiento']:
        Movim: 'Movimiento' = self.get_related_class('cuentas').get_related_class('entradas')
        return Movim.filtro(
            Q(cta_entrada__in=self.cuentas.all()) |
            Q(cta_salida__in=self.cuentas.all()) |
            Q(cta_entrada__in=self.ex_cuentas.all()) |
            Q(cta_salida__in=self.ex_cuentas.all())
        )

    def clean(self):
        super().clean()
        self.nombre = self.nombre or self.sk
        self._validar_sk()

    def delete(self, *args, **kwargs):
        if self.capital() != 0:
            raise errors.SaldoNoCeroException
        if self.movs().exists():
            raise errors.ExistenMovimientosException
        super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return self.nombre

    def es_acreedor_de(self, otro: Self) -> bool:
        return self in otro.acreedores.all()

    def es_deudor_de(self, otro: Self) -> bool:
        return self in otro.deudores.all()

    def cuenta_credito_con(self, otro: Self) -> Optional['CuentaInteractiva']:
        try:
            return self.cuentas.get(sk=f'_{self.sk}-{otro.sk}')
        except self.get_related_class('cuentas').DoesNotExist:
            return None

    def deuda_con(self, otro: Self) -> float:
        if self in otro.deudores.all():
            return -self.cuenta_credito_con(otro).saldo()
        return 0

    def cancelar_deuda_de(self, otro: Self):
        if otro not in self.deudores.all():
            raise self.get_class().DoesNotExist(
                f'{otro} no figura entre los deudores de {self}'
            )
        self.deudores.remove(otro)

    def _validar_sk(self):
        self.sk = mi_slugify(
            self.sk, reemplazo='_')
        if '-' in self.sk:
            raise ValidationError('No se admite guión en sk')
