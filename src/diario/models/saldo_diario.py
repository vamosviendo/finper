from __future__ import annotations
from typing import TYPE_CHECKING, Self, Iterable

from django.db import models, transaction

from vvmodel.models import MiModel

if TYPE_CHECKING:
    from diario.models import Movimiento, Cuenta, Dia


class SaldoDiario(MiModel):
    cuenta = models.ForeignKey('diario.Cuenta', on_delete=models.CASCADE)
    dia = models.ForeignKey('diario.Dia', on_delete=models.CASCADE)
    _importe = models.FloatField()
    sk = models.CharField(max_length=25, null=True, blank=True, unique=True)

    class Meta:
        unique_together = ['cuenta', 'dia']
        ordering = ['dia']

    def __str__(self):
        return f"{self.cuenta} al {self.dia}: {self.importe}"

    @property
    def importe(self) -> float:
        return self._importe

    @importe.setter
    def importe(self, value: float):
        self._importe = round(value, 2)

    @classmethod
    def anterior_a(cls, cuenta: Cuenta, dia: Dia):
        return cls.filtro(cuenta_id=cuenta.pk, dia__fecha__lt=dia.fecha).last()

    @classmethod
    def calcular(cls, mov: Movimiento, sentido: str | None = None):
        if sentido is None:
            if mov.cta_entrada is None:
                sentido = "salida"
            elif mov.cta_salida is None:
                sentido = "entrada"
            else:
                raise ValueError('En un movimiento de traspaso debe especificarse argumento "sentido"')

        if sentido.startswith("cta_"):
            sentido = sentido[4:]
        if sentido not in ("entrada", "salida"):
            raise ValueError(
                'Los valores aceptados para arg "sentido" son "entrada", "cta_entrada", "salida", "cta_salida"'
            )

        cuenta = getattr(mov, f"cta_{sentido}")
        importe_mov = mov.importe_cta(sentido)

        try:
            saldo_diario = cls.tomar(cuenta=cuenta, dia=mov.dia)
            saldo_diario.importe += importe_mov
            saldo_diario.clean_save()
        except cls.DoesNotExist:
            try:
                importe = cls.anterior_a(cuenta=cuenta, dia=mov.dia).importe + importe_mov
            except AttributeError:  # No hay saldo diario anterior
                importe = importe_mov
            saldo_diario = cls.crear(cuenta=cuenta, dia=mov.dia, importe=importe)

        return saldo_diario

    @classmethod
    def indexar_por_dia(cls, cuentas: Iterable[Cuenta], dia: Dia):
        saldos_diarios = {
            sd.cuenta_id: sd.importe
            for sd in SaldoDiario.filtro(cuenta__in=cuentas, dia=dia)
        }

        cuentas_sin_sd = [c for c in cuentas if c.pk not in saldos_diarios]
        if cuentas_sin_sd:
            sds_anteriores = SaldoDiario.filtro(
                cuenta__in=cuentas_sin_sd,
                dia__fecha__lt=dia.fecha,
            ).order_by('cuenta_id', '-dia__fecha')
            vistos = set()
            for sd in sds_anteriores:
                if sd.cuenta_id not in vistos:
                    saldos_diarios[sd.cuenta_id] = sd.importe
                    vistos.add(sd.cuenta_id)

        return saldos_diarios

    @classmethod
    def indexar_en_movimiento(
            cls,
            cuentas: Iterable[Cuenta],
            movimiento: Movimiento) -> dict[int, float]:
        from diario.models import Movimiento

        saldos_diarios = cls.indexar_por_dia(cuentas, movimiento.dia)

        movs_posteriores = list(Movimiento.filtro(
            dia=movimiento.dia,
            orden_dia__gt=movimiento.orden_dia,
        ).select_related('cta_entrada', 'cta_salida'))

        ids_cuentas = {c.pk for c in cuentas}
        ajustes = {c.pk: 0.0 for c in cuentas}
        for mov in movs_posteriores:
            if mov.cta_entrada_id in ids_cuentas:
                ajustes[mov.cta_entrada_id] -= mov.importe_cta_entrada
            if mov.cta_salida_id in ids_cuentas:
                ajustes[mov.cta_salida_id] -= mov.importe_cta_salida

        return {
            cuenta_id: importe + ajustes[cuenta_id]
            for cuenta_id, importe in {
                c.pk: saldos_diarios.get(c.pk, 0.0) for c in cuentas
            }.items()
        }

    def anterior(self):
        return SaldoDiario.anterior_a(cuenta=self.cuenta, dia=self.dia)

    @transaction.atomic
    def eliminar(self):
        importe = self.importe
        try:
            importe_anterior = self.anterior().importe
        except AttributeError:
            importe_anterior = 0
        self.delete()
        self._actualizar_posteriores(importe_anterior-importe)

    def clean_save(
            self, exclude=None, validate_unique=True, validate_constraints=True,
            force_insert=False, force_update=False, using=None, update_fields=None,
            actualizar_posteriores=True
    ):
        super().full_clean(exclude, validate_unique, validate_constraints)
        self.save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields,
                  actualizar_posteriores=actualizar_posteriores)

    @transaction.atomic
    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None,
            actualizar_posteriores=True
    ):
        # Generar sk si no existe
        if self.sk is None:
            self.sk = f"{self.dia.sk}{self.cuenta.sk}"

        if self._state.adding:
            try:
                importe_anterior = self.anterior().importe
                importe = self.importe - importe_anterior
            except AttributeError:  # No hay movimiento anterior.
                importe = self.importe
            self._actualizar_posteriores(importe)

        else:
            if self.cambia_campo("_importe"):
                importe_guardado = self.tomar_de_bd().importe
                importe = self.importe - importe_guardado
                if actualizar_posteriores:
                    self._actualizar_posteriores(importe)

        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

    def tomar_de_bd(self) -> Self:
        return self.get_class().tomar_o_nada(cuenta=self.cuenta, dia=self.dia)

    # Métodos protegidos
    def _actualizar_posteriores(self, importe):
        for sd in SaldoDiario.filtro(cuenta=self.cuenta, dia__fecha__gt=self.dia.fecha):
            sd.importe += importe

            sd.clean_save(actualizar_posteriores=False)
