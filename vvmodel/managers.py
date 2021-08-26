from django.core.exceptions import SuspiciousOperation
from django.db import models
from django.db.models.query import QuerySet

from .errors import ERROR_QUERYSET_DELETE


class MiQuerySet(QuerySet):

    def delete(self):
        """ Impide que se eliminen todos los registros de un query sin un bucle}
            for (con Model.objects.all().delete(), por ejemplo)."""
        raise SuspiciousOperation(ERROR_QUERYSET_DELETE)


class PolymorphQuerySet(MiQuerySet):
    """ QuerySet polimórfico, devuelve objetos conservando la subclase en la
        que fueron salvados."""

    def __getitem__(self, k):
        result = super().__getitem__(k)
        if isinstance(result, models.Model):
            return result.como_subclase(db=result._state.db)
        return result

    def __iter__(self):
        for item in super().__iter__():
            yield item.como_subclase(db=item._state.db)


class PolymorphManager(models.Manager):

    def get_queryset(self):
        pqs = PolymorphQuerySet(self.model)
        if self._db is not None:
            pqs = pqs.using(self._db)
        return pqs

    def get(self, *args, **kwargs):
        item = super().get(*args, **kwargs)
        return item.como_subclase(db=item._state.db)

    def get_no_poly(self, *args, **kwargs):
        """ get() no polimórfico. No tiene en cuenta la subclase"""
        return super().get(*args, **kwargs)
