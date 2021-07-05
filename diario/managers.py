from django.db import models


class PolymorphQuerySet(models.query.QuerySet):

    def __getitem__(self, k):
        item = super().__getitem__(k)
        if isinstance(item, models.Model):
            return item.como_subclase(database=item._state.db)
        return item

    def __iter__(self):
        for item in super().__iter__():
            yield item.como_subclase(database=item._state.db)


class PolymorphManager(models.Manager):

    def get_queryset(self):
        queryset = PolymorphQuerySet(self.model)
        if self._db is not None:
            queryset = queryset.using(self._db)
        return queryset

    def get(self, *args, **kwargs):
        item = super().get(*args, **kwargs)
        return item.como_subclase(database=item._state.db)

    def get_no_poly(self, *args, **kwargs):
        return super().get(*args, **kwargs)