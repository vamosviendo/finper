from __future__ import annotations

from datetime import date
from typing import Iterable, TYPE_CHECKING

from django.core.exceptions import EmptyResultSet, ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from vvmodel.cleaners import Cleaner
from utils.varios import el_que_no_es
from vvmodel.models import MiModel

if TYPE_CHECKING:
    from diario.models import Cuenta, Moneda


class CotizacionCleaner(Cleaner):
    def no_admite_importe_vacio(self):
        if self.obj.importe_compra is None and self.obj.importe_venta is None:
            raise ValidationError("Debe ingresar al menos un importe")


class Cotizacion(MiModel):
    importe_compra = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    importe_venta = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    fecha = models.DateField()
    moneda = models.ForeignKey("diario.Moneda", related_name="cotizaciones", on_delete=models.CASCADE)
    sk = models.CharField(max_length=20, null=True, blank=True, unique=True)

    form_fields = ['fecha', 'importe_compra', 'importe_venta']
    cleaner = CotizacionCleaner

    class Meta:
        ordering = ("fecha", )
        unique_together = ("fecha", "moneda", )

    def __str__(self):
        return f"Cotización {self.moneda} al {self.fecha}: {self.importe_compra} / {self.importe_venta}"

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

    @classmethod
    def indexar(
            cls,
            cuentas: Iterable[Cuenta],
            monedas: Iterable[Moneda],
            fecha: date
    ) -> dict[tuple[int, int], float]:
        ids_monedas_origen = {c.moneda_id for c in cuentas}
        monedas_todas_ids = list({*ids_monedas_origen, *[m.pk for m in monedas]})
        cots_raw = Cotizacion.filtro(
            moneda__in=monedas_todas_ids,
            fecha__lte=fecha,
        ).order_by('moneda_id', '-fecha')
        vistos = set()
        cots_por_moneda = {}
        for cot in cots_raw:
            if cot.moneda_id not in vistos:
                cots_por_moneda[cot.moneda_id] = cot
                vistos.add(cot.moneda_id)

        cotizaciones = {}
        for id_moneda_origen in ids_monedas_origen:
            for moneda_destino in monedas:
                if id_moneda_origen == moneda_destino.pk:
                    cotizaciones[(id_moneda_origen, moneda_destino.pk)] = 1.0
                else:
                    cot_orig = cots_por_moneda.get(id_moneda_origen)
                    cot_dest = cots_por_moneda.get(moneda_destino.pk)
                    if cot_orig and cot_dest:
                        cotizaciones[(id_moneda_origen, moneda_destino.pk)] = (
                                cot_orig.importe_venta / cot_dest.importe_compra
                        )
                    else:
                        cotizaciones[(id_moneda_origen, moneda_destino.pk)] = 1.0

        return cotizaciones

    def save(self, *args, **kwargs):
        # Generar clave secundaria
        if self.sk is None:
            self.sk = f"{self.fecha.strftime('%Y%m%d')}{self.moneda.sk}"

        # Si hay algún importe vacío, completar con importe existente
        for tipo in "importe_compra", "importe_venta":
            tipo_opuesto = el_que_no_es(tipo, "importe_compra", "importe_venta")
            importe = getattr(self, tipo)
            importe_opuesto = getattr(self, tipo_opuesto)
            if importe is None and importe_opuesto is not None:
                setattr(self, tipo, importe_opuesto)
        super().save(*args, **kwargs)
