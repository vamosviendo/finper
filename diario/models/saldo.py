"""
Hay un saldo por cuenta y por movimiento (hasta dos cuentas por movimiento).
El campo _importe podría no existir, y surgir de sumar el saldo anterior y
el importe del movimiento (o restarlo en caso de que la cuenta fuera de salida),
pero si hiciéramos eso dejaría de tener sentido la existencia del modelo Saldo,
ya que equivaldría a calcular todos los saldos históricos al momento de
mostrarlos.
(De todos modos no estaría mal hacer un branch basado en el cálculo y no en
la consulta a base de datos y ver cuál es más rápido, en una de esas calcular
es más rápido y hago desaparecer este modelo).
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
            saldo = cls.crear(
                cuenta=cuenta,
                importe=importe_saldo_anterior + importe,
                movimiento=mov
            )
            saldo._actualizar_posteriores(importe)

            return saldo

        return None

    def eliminar(self):
        self.delete()
        try:
            importe_anterior = self.anterior().importe
        except AttributeError:
            importe_anterior = 0
        importe = self.importe - importe_anterior
        self._actualizar_posteriores(-importe)

    def anterior(self):
        return Saldo._anterior_a(
            self.movimiento.fecha,
            self.movimiento.orden_dia,
            self.cuenta
        )

    def anteriores(self):
        return Saldo._anteriores_a(
            self.movimiento.fecha,
            self.movimiento.orden_dia,
            self.cuenta
        )

    def posteriores(self):
        return Saldo._posteriores_a(
            self.movimiento.fecha,
            self.movimiento.orden_dia,
            self.cuenta
        )

    def sumar_a_este_y_posteriores(self, importe):
        self._actualizar_posteriores(importe)
        self.importe += importe
        self.save()

    @staticmethod
    def _anterior_a(fecha, orden_dia, cuenta):
        return Saldo._anteriores_a(fecha, orden_dia, cuenta).last()

    @staticmethod
    def _anteriores_a(fecha, orden_dia, cuenta):
        return cuenta.saldo_set.filter(
            movimiento__fecha__lt=fecha
        ) | cuenta.saldo_set.filter(
            movimiento__fecha=fecha,
            movimiento__orden_dia__lt=orden_dia
        )

    @staticmethod
    def _posteriores_a(fecha, orden_dia, cuenta):
        return cuenta.saldo_set.filter(
            movimiento__fecha__gt=fecha
        ) | cuenta.saldo_set.filter(
            movimiento__fecha=fecha,
            movimiento__orden_dia__gt=orden_dia
        )

    def _actualizar_posteriores(self, importe):
        for saldo_post in self.posteriores():
                saldo_post.importe += importe
                saldo_post.save()
