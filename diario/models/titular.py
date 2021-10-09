from django.db import models

from diario.settings_app import TITULAR_PRINCIPAL
from vvmodel.models import MiModel


class Titular(MiModel):
    titname = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100, blank=True)

    def full_clean(self, exclude=None, validate_unique=True):
        self.nombre = self.nombre or self.titname
        super().full_clean(exclude=None, validate_unique=True)

    @classmethod
    def por_defecto(cls):
        titular, created = cls.objects.get_or_create(
            titname=TITULAR_PRINCIPAL['titname'],
            nombre=TITULAR_PRINCIPAL['nombre'],
        )
        return titular.pk
