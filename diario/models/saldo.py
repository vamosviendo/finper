"""
Hay un saldo por cuenta y por fecha.
El saldo de la fecha de una cuenta se usa para calcular el saldo al momento
de cada movimiento de la fecha.
"""
from django.db import models

from vvmodel.models import MiModel


class Saldo(MiModel):

    cuenta = models.ForeignKey('diario.Cuenta', on_delete=models.CASCADE)
    # fecha = models.DateField()
    movimiento = models.ForeignKey(
        'diario.Movimiento', on_delete=models.CASCADE)
    _importe = models.FloatField()

    class Meta:
        unique_together = ['cuenta', 'movimiento']
        ordering = ['movimiento']

    def __str__(self):
        return f'{self.cuenta} al {self.movimiento.fecha} - {self.movimiento.orden_dia+1}: {self.importe}'

    @property
    def importe(self):
        return self._importe

    @importe.setter
    def importe(self, valor):
        self._importe = round(valor, 2)

    @classmethod
    def tomar(cls, **kwargs):
        cuenta = kwargs['cuenta']
        movimiento = kwargs['movimiento']

        if cuenta.es_acumulativa:
            importe = 0
            for c in cuenta.subcuentas.all():
                try:
                    importe += Saldo.tomar(cuenta=c, movimiento=movimiento).importe
                except Saldo.DoesNotExist:
                    pass
            return Saldo(cuenta=cuenta, movimiento=movimiento, importe=importe)

        try:
            return super().tomar(**kwargs)
        except cls.DoesNotExist:
            result = Saldo._anterior_a(
                fecha=movimiento.fecha,
                orden_dia=movimiento.orden_dia,
                cuenta=cuenta
            )

            if result is None:
                raise cls.DoesNotExist

            return result

    @classmethod
    def tomar_de_fecha(cls, cuenta, fecha):
        ultimo_mov = Saldo.get_related_class('movimiento')\
            .filtro(fecha__lte=fecha)\
            .last()
        return Saldo.tomar(cuenta=cuenta, movimiento=ultimo_mov)

    @classmethod
    def generar(cls, mov, salida):

        cuenta = mov.cta_salida if salida else mov.cta_entrada
        importe = mov.importe if not salida else -mov.importe

        if cuenta:
            try:
                importe_saldo_anterior = Saldo._anterior_a(
                    mov.fecha, mov.orden_dia, cuenta
                ).importe
            except AttributeError:
                importe_saldo_anterior = 0
            result = cls.crear(
                cuenta=cuenta,
                importe=importe_saldo_anterior + importe,
                movimiento=mov
            )
            Saldo._actualizar_posteriores(cuenta, mov, importe)

            return result

        return None

    def eliminar(self):
        self.delete()
        try:
            importe_anterior = self.anterior().importe
        except AttributeError:
            importe_anterior = 0
        importe = self.importe - importe_anterior
        Saldo._actualizar_posteriores(
            self.cuenta, self.movimiento, -importe)

    def anterior(self):
        return Saldo._anterior_a(
            self.movimiento.fecha,
            self.movimiento.orden_dia,
            self.cuenta
        )

    @staticmethod
    def _anterior_a(fecha, orden_dia, cuenta):
        anteriores = cuenta.saldo_set.filter(
            movimiento__fecha__lt=fecha
        ) | cuenta.saldo_set.filter(
            movimiento__fecha=fecha,
            movimiento__orden_dia__lt=orden_dia
        )
        return anteriores.last()

    @staticmethod
    def _actualizar_posteriores(cuenta, mov, importe):

        # TODO: Refactor. Definir < y > para Movimiento.
        for saldo_post in Saldo.filtro(
                cuenta=cuenta,
                movimiento__fecha__gt=mov.fecha
        ) | Saldo.filtro(
            cuenta=cuenta,
            movimiento__fecha=mov.fecha,
            movimiento__orden_dia__gt=mov.orden_dia
        ):
                saldo_post.importe += importe
                saldo_post.save()
