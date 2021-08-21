from django.contrib.contenttypes.models import ContentType
from django.db import models

from .managers import PolymorphManager


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
    def tomar(cls, polymorphic=True, *args, **kwargs):
        try:
            using = kwargs.pop('using')
        except KeyError:
            using = 'default'

        if polymorphic:
            return cls.objects.db_manager(using).get(*args, **kwargs)
        return cls.objects.db_manager(using).get_no_poly(*args, **kwargs)

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

    @classmethod
    def get_class(cls):
        return cls

    @classmethod
    def get_class_name(cls):
        return cls.__name__

    @classmethod
    def get_lower_class_name(cls):
        return cls.get_class_name().lower()

    def update_from(self, objeto, commit=True):
        for campo in objeto.get_class()._meta.fields:
            valor = campo.value_from_object(objeto)
            if valor is not None:
                try:
                    setattr(self, campo.name, valor)
                except ValueError:
                    # Suponemos que es un campo de tipo foreign
                    setattr(
                        self, campo.name,
                        self._meta
                            .get_field(campo.name)
                            .remote_field
                            .model
                            .tomar(pk=valor)
                    )

        if commit:
            self.save()

        return self


class PolymorphModel(MiModel):
    """ Agrega polimorfismo a MiModel."""

    class Meta:
        abstract = True

    content_type = models.ForeignKey(
        ContentType,
        null=True,
        editable=False,
        on_delete=models.CASCADE,
    )

    objects = PolymorphManager()

    def como_subclase(self, db='default'):
        """ Devuelve objeto polimórfico, basándose en el campo content_type.
            Arg db: corrige un error (¿bug?) que se produce cuando se intenta
            eliminar todos los registros de la clase madre (ver punto 2 en
            comentario inicial de sda.managers).
        """
        content_type = self.content_type
        model = content_type.model_class()
        return model.tomar(pk=self.pk, polymorphic=False, using=db)

    def save(self, *args, using='default', **kwargs):

        if not self.content_type:
            ct = ContentType.objects.db_manager(using).get(
                app_label=self._meta.app_label,
                model=self.get_lower_class_name()
            )
            self.content_type = ct

        super().save(*args, **kwargs)
