from __future__ import annotations
from typing import TYPE_CHECKING, Self

from django.db import models

from vvmodel.models import MiModel

if TYPE_CHECKING:
    from diario.models import Movimiento, Cuenta, Dia


class SaldoDiario(MiModel):
    cuenta = models.ForeignKey('diario.Cuenta', on_delete=models.CASCADE)
    dia = models.ForeignKey('diario.Dia', on_delete=models.CASCADE)
    _importe = models.FloatField()

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

    @property
    def sk(self) -> str:
        return f"{self.dia.sk}{self.cuenta.sk}"

    @classmethod
    def anterior_a(cls, cuenta: Cuenta, dia: Dia):
        return cls.filtro(cuenta=cuenta, dia__fecha__lt=dia.fecha).last()

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
        importe_mov = getattr(mov, f"importe_cta_{sentido}")

        try:
            saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
            saldo_diario.importe += importe_mov
            saldo_diario.clean_save()
        except cls.DoesNotExist:
            try:
                importe = cls.anterior_a(cuenta=cuenta, dia=mov.dia).importe + importe_mov
            except AttributeError:  # No hay saldo diario anterior
                importe = importe_mov
            saldo_diario = cls.crear(cuenta=cuenta, dia=mov.dia, importe=importe)

        return saldo_diario

    def anterior(self):
        return SaldoDiario.anterior_a(cuenta=self.cuenta, dia=self.dia)

    def eliminar(self):
        importe = self.importe
        self.delete()
        self._actualizar_posteriores(-importe)

    def save(self, *args, **kwargs):
        if self._state.adding:
            try:
                importe_anterior = self.anterior_a(self.cuenta, self.dia).importe
                importe = self.importe - importe_anterior
            except AttributeError:  # No hay movimiento anterior.
                importe = self.importe
            self._actualizar_posteriores(importe)

        else:
            if self.cambia_campo("_importe"):
                importe_guardado = self.tomar_de_bd().importe
                importe = self.importe - importe_guardado
                self._actualizar_posteriores(importe)

        return super().save(*args, **kwargs)

    def cambia_campo(self, *args, contraparte: Movimiento = None) -> bool:
        mov_guardado = contraparte or self.tomar_de_bd()
        for campo in args:
            if campo not in [x.name for x in self._meta.fields]:
                raise ValueError(f"Campo inexistente: {campo}")
            try:
                if getattr(self, campo) != getattr(mov_guardado, campo):
                    return True
            except AttributeError:  # mov_guardado == None => El movimiento es nuevo.
                return True
        return False

    def tomar_de_bd(self) -> Self:
        return self.get_class().tomar_o_nada(cuenta=self.cuenta, dia=self.dia)

    # Métodos protegidos
    def _actualizar_posteriores(self, importe):
        for sd in SaldoDiario.filtro(cuenta=self.cuenta, dia__fecha__gt=self.dia.fecha):
            sd.importe += importe
            sd.clean_save()
