from __future__ import annotations

from typing import TYPE_CHECKING, Self, Optional, Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet, Q
from django.utils import timezone

from vvmodel.models import MiModel
from vvutils.text import mi_slugify

from diario.models.dia import Dia

if TYPE_CHECKING:
    from diario.models import CuentaAcumulativa, CuentaInteractiva, Movimiento
    from diario.models.cuenta import CuentaManager


class TitularManager(models.Manager):
    def get_by_natural_key(self, sk):
        return self.get(_sk=sk)

class Titular(MiModel):
    _sk = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100, blank=True)
    fecha_alta = models.DateField(default=timezone.now)
    deudores = models.ManyToManyField('Titular', related_name='acreedores')

    acreedores: TitularManager["Titular"]           # related name para campo deudores
    cuentas: CuentaManager["CuentaInteractiva"]     # related name para CuentaInteractiva.titular
    ex_cuentas: CuentaManager["CuentaAcumulativa"]  # related name para CuentaAcumulativa.titular_original

    objects = TitularManager()
    form_fields = ('sk', 'nombre', 'fecha_alta', )

    def natural_key(self) -> tuple[str]:
        return (self.sk, )

    @property
    def sk(self) -> str:
        return self._sk

    @sk.setter
    def sk(self, value: str):
        self._sk = value

    @classmethod
    def tomar(self, **kwargs):
        if "sk" in kwargs.keys():
            kwargs["_sk"] = kwargs.pop("sk")
        return super().tomar(**kwargs)

    def capital(self, movimiento: 'Movimiento' = None, dia: Dia = None) -> float:
        if movimiento:
            return sum(c.saldo(movimiento=movimiento) for c in self.cuentas_interactivas())
        if dia:
            return sum(c.saldo(dia=dia) for c in self.cuentas_interactivas())
        return sum(c.saldo() for c in self.cuentas_interactivas())

    def cuentas_interactivas(self) -> models.QuerySet['CuentaInteractiva']:
        ids = [c.id for c in self.cuentas.all() if c.es_interactiva]
        return self.cuentas.filter(id__in=ids)

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

    def __str__(self) -> str:
        return self.nombre

    def es_acreedor_de(self, otro: Self) -> bool:
        return self in otro.acreedores.all()

    def es_deudor_de(self, otro: Self) -> bool:
        return self in otro.deudores.all()

    def cuenta_credito_con(self, otro: Self) -> Optional['CuentaInteractiva']:
        try:
            return self.cuentas.get(_sk=f'_{self.sk}-{otro.sk}')
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
