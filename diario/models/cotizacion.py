from datetime import date

from django.core.exceptions import EmptyResultSet, ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from utils.varios import el_que_no_es
from vvmodel.models import MiModel


class Cotizacion(MiModel):
    importe_compra = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    importe_venta = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    fecha = models.DateField()
    moneda = models.ForeignKey("diario.Moneda", related_name="cotizaciones", on_delete=models.CASCADE)

    form_fields = ['fecha', 'importe_compra', 'importe_venta']

    class Meta:
        ordering = ("fecha", )
        unique_together = ("fecha", "moneda", )

    def __str__(self):
        return f"Cotización {self.moneda} al {self.fecha}: {self.importe_compra} / {self.importe_venta}"

    @property
    def sk(self) -> str:
        return f"{self.fecha.year}{self.fecha.month}{self.fecha.day}{self.moneda.sk}"

    def get_delete_url(self) -> str:
        return reverse("cot_elim", args=[self.sk])

    def get_edit_url(self) -> str:
        return reverse("cot_mod", args=[self.sk])

    @classmethod
    def tomar(cls, **kwargs):
        kwargs["fecha"] = kwargs.get("fecha") or date.today()

        if "moneda" not in kwargs.keys():
            raise TypeError('Argumento "moneda" faltante')
        for key in kwargs.keys():
            if key not in ("moneda", "fecha"):
                raise TypeError(f'Argumento "{key}" inesperado')

        try:
            return super().tomar(**kwargs)
        except cls.DoesNotExist:
            cotizaciones_anteriores = cls.filtro(moneda=kwargs["moneda"], fecha__lt=kwargs["fecha"])
            if cotizaciones_anteriores.exists():
                return cotizaciones_anteriores.last()
            raise EmptyResultSet(
                f"No hay cotizaciones de {kwargs['moneda']} anteriores al {kwargs['fecha']}"
            )

    def clean(self):
        super().clean()
        if self.importe_compra is None and self.importe_venta is None:
            raise ValidationError("Debe ingresar al menos un importe")

    def save(self, *args, **kwargs):
        for tipo in "importe_compra", "importe_venta":
            tipo_opuesto = el_que_no_es(tipo, "importe_compra", "importe_venta")
            importe = getattr(self, tipo)
            importe_opuesto = getattr(self, tipo_opuesto)
            if importe is None and importe_opuesto is not None:
                setattr(self, tipo, importe_opuesto)
        super().save(*args, **kwargs)
