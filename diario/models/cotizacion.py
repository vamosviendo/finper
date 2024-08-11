from datetime import date

from django.db import models

from vvmodel.models import MiModel


class Cotizacion(MiModel):
    importe = models.FloatField()
    fecha = models.DateField()
    moneda = models.ForeignKey("diario.Moneda", related_name="cotizaciones", on_delete=models.CASCADE)

    class Meta:
        ordering = ("fecha", )
        unique_together = ("fecha", "moneda", )

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
            return cls.filtro(moneda=kwargs["moneda"], fecha__lt=kwargs["fecha"]).last()
