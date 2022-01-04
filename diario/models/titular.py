from django.db import models
from django.db.models import Sum

from diario.settings_app import TITULAR_PRINCIPAL
from vvmodel.models import MiModel


class Titular(MiModel):
    titname = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100, blank=True)
    deudores = models.ManyToManyField('Titular', related_name='acreedores')

    @property
    def patrimonio(self):
        return self.cuentas.all().aggregate(Sum('_saldo'))['_saldo__sum'] or 0

    def movimientos(self):
        lista_movimientos = list()
        for cuenta in self.cuentas.all():
            lista_movimientos += cuenta.movs_directos()
        lista_movimientos = list(set(lista_movimientos))
        lista_movimientos.sort(key=lambda x: (x.fecha, x.orden_dia))
        return lista_movimientos

    def full_clean(self, exclude=None, validate_unique=True):
        self.nombre = self.nombre or self.titname
        super().full_clean(exclude=None, validate_unique=True)

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

    # TODO: Pasar a MiModel
    @classmethod
    def modelo_relacionado_con(cls, campo):
        return cls._meta.get_field(campo).related_model

    def cancelar_deuda_de(self, otro):
        if otro not in self.deudores.all():
            raise self.get_class().DoesNotExist(
                f'{otro} no figura entre los deudores de {self}'
            )
        self.deudores.remove(otro)
