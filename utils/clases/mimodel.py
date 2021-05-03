from django.db import models


class MiModel(models.Model):

    class Meta:
        abstract = True

    @classmethod
    def todes(cls, using='default'):
        return cls.objects.using(using).all()

    @classmethod
    def primere(cls, using='default'):
        return cls.objects.using(using).first()

    @classmethod
    def tomar(cls, *args, **kwargs):
        try:
            using = kwargs.pop('using')
        except KeyError:
            using = 'default'
        return cls.objects.db_manager(using).get(*args, **kwargs)

    @classmethod
    def cantidad(cls, using='default'):
        return cls.objects.using(using).count()

    @classmethod
    def excepto(cls, *args, **kwargs):
        try:
            using = kwargs.pop('using')
        except KeyError:
            using = 'default'
        return cls.objects.using(using).exclude(*args, **kwargs)

    @classmethod
    def filtro(cls, *args, **kwargs):
        try:
            using = kwargs.pop('using')
        except KeyError:
            using = 'default'
        return cls.objects.using(using).filter(*args, **kwargs)

    @classmethod
    def crear(cls, **kwargs):
        try:
            using = kwargs.pop('using')
        except KeyError:
            using = 'default'
        obj = cls(**kwargs)
        obj.full_clean()
        obj.save()
        return obj
