from datetime import date

from django.db import models

from vvmodel.models import MiModel, PolymorphModel


class MiTestRelatedModel(MiModel):
    nombre = models.CharField(max_length=50, unique=True)


class MiTestModel(MiModel):
    nombre = models.CharField(max_length=50, unique=True)
    numero = models.FloatField()
    fecha = models.DateField(default=date.today)
    related = models.ForeignKey(MiTestRelatedModel, on_delete=models.CASCADE)


class MiTestPolymorphModel(PolymorphModel):
    nombre = models.CharField(max_length=50, unique=True)
    numero = models.FloatField()


class MiTestPolymorphSubmodel(MiTestPolymorphModel):
    detalle = models.TextField()


class MiTestPolymorphSubSubModel(MiTestPolymorphSubmodel):
    pass
