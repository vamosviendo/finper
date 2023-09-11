from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet, Q

from diario.settings_app import TITULAR_PRINCIPAL
from vvmodel.models import MiModel
from vvutils.text import mi_slugify


class Titular(MiModel):
    titname = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100, blank=True)
    deudores = models.ManyToManyField('Titular', related_name='acreedores')

    @property
    def capital(self):
        return sum([c.saldo for c in self.cuentas_interactivas()])

    def capital_historico(self, movimiento):
        return sum(c.saldo_en_mov(movimiento) for c in self.cuentas_interactivas())

    def cuentas_interactivas(self):
        ids = [c.id for c in self.cuentas.all() if c.es_interactiva]
        return self.cuentas.filter(id__in=ids)

    def movs(self) -> QuerySet:
        Movimiento = self.get_related_class('cuentas').get_related_class('entradas')
        return Movimiento.filtro(
            Q(cta_entrada__in=self.cuentas.all()) |
            Q(cta_salida__in=self.cuentas.all()) |
            Q(cta_entrada__in=self.ex_cuentas.all()) |
            Q(cta_salida__in=self.ex_cuentas.all())
        )

    def clean(self):
        super().clean()
        self.nombre = self.nombre or self.titname
        self._validar_titname()

    def __str__(self):
        return self.nombre

    @classmethod
    def por_defecto(cls):
        titular, created = cls.objects.get_or_create(
            titname=TITULAR_PRINCIPAL['titname'],
            nombre=TITULAR_PRINCIPAL['nombre'],
        )
        return titular.pk

    @classmethod
    def tomar_o_default(cls, **kwargs):
        try:
            return cls.tomar(**kwargs)
        except cls.DoesNotExist:
            return cls.tomar(pk=cls.por_defecto())

    def es_acreedor_de(self, otro):
        return self in otro.acreedores.all()

    def es_deudor_de(self, otro):
        return self in otro.deudores.all()

    def cuenta_credito_con(self, otro):
        try:
            return self.cuentas.get(slug=f'_{self.titname}-{otro.titname}')
        except self.get_related_class('cuentas').DoesNotExist:
            return None

    def deuda_con(self, otro):
        if self in otro.deudores.all():
            return -self.cuenta_credito_con(otro).saldo
        return 0

    def cancelar_deuda_de(self, otro):
        if otro not in self.deudores.all():
            raise self.get_class().DoesNotExist(
                f'{otro} no figura entre los deudores de {self}'
            )
        self.deudores.remove(otro)

    def _validar_titname(self):
        self.titname = mi_slugify(
            self.titname, reemplazo='_')
        if '-' in self.titname:
            raise ValidationError('No se admite guión en titname')

    def as_view_context(self, movimiento=None, es_elemento_principal=False):

        context = {
            'titname': self.titname,
            'nombre': self.nombre,
            'capital': self.capital_historico(movimiento) if movimiento
                else self.capital,
            'movimientos': [x.as_view_context() for x in self.movs()],
        }
        if es_elemento_principal:
            context.update({
                'cuentas':
                    [x.as_view_context(movimiento) for x in self.cuentas.all()],
            })

        return context
