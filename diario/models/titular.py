from django.db import models

from vvmodel.models import MiModel


class Titular(MiModel):
    titname = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100, blank=True)

    def full_clean(self, exclude=None, validate_unique=True):
        self.nombre = self.nombre or self.titname
        super().full_clean(exclude=None, validate_unique=True)
