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
    importe = models.FloatField()

    class Meta:
        unique_together = ['cuenta', 'movimiento']
        ordering = ['movimiento']

    def __str__(self):
        return f'{self.cuenta} al {self.movimiento.fecha} - {self.movimiento.orden_dia+1}: {self.importe}'

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
            result = Saldo.filtro(
                cuenta=cuenta,
                movimiento__lt=movimiento
            ).last()

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
                importe_saldo_anterior = cuenta.saldo_set\
                    .filter(movimiento__lt=mov)\
                    .last()\
                    .importe
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
        # TODO: Refactor - escribir método Saldo.anterior()
        try:
            importe_anterior = self.cuenta.saldo_set.filter(movimiento__lt=self.movimiento).last().importe
        except AttributeError:
            importe_anterior = 0
        importe = self.importe - importe_anterior
        Saldo._actualizar_posteriores(
            self.cuenta, self.movimiento, -importe)

    @staticmethod
    def _actualizar_posteriores(cuenta, mov, importe):

        # TODO: Refactor. Definir < y > para Movimiento.
        #       (¿Por qué no funcionaría un filtro(cuenta=cuenta, movimiento__gt=mov))
        for saldo_post in Saldo.filtro(cuenta=cuenta):
            if saldo_post.movimiento.fecha > mov.fecha or (
                    saldo_post.movimiento.fecha == mov.fecha and
                    saldo_post.movimiento.orden_dia > mov.orden_dia
            ):
                saldo_post.importe += importe
                saldo_post.save()
