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
        try:
            return super().tomar(**kwargs)
        except cls.DoesNotExist:
            result = Saldo.filtro(
                cuenta=kwargs['cuenta'],
                movimiento__lt=kwargs['movimiento']
            ).last()

            if result is None:
                raise cls.DoesNotExist

            return result

    @classmethod
    def generar(cls, mov):
        saldo_ce = saldo_cs = None

        if mov.cta_entrada:
            try:
                importe_saldo_anterior = mov.cta_entrada.saldo_set\
                    .filter(movimiento__lt=mov)\
                    .last()\
                    .importe
            except AttributeError:
                importe_saldo_anterior = 0
            saldo_ce = cls.crear(
                cuenta=mov.cta_entrada,
                importe=importe_saldo_anterior + mov.importe,
                movimiento=mov
            )
            Saldo._actualizar_posteriores(mov.cta_entrada, mov, mov.importe)

            # TODO: Esto no es óptimo. Puede ser confuso. Lo ideal sería que
            #   las cuentas acumulativas no tuvieran saldos como objeto sino que se manejaran
            #   directamente con importes de saldo (aunque todavía no tengo muy
            #   claro qué significaría o implicaría esto)
            for cta_ancestro in mov.cta_entrada.ancestros():
                cls.crear(
                    cuenta=cta_ancestro,
                    movimiento=mov,
                    importe=saldo_ce.importe
                )

        if mov.cta_salida:
            try:
                importe_saldo_anterior = mov.cta_salida.saldo_set\
                    .filter(movimiento__lt=mov)\
                    .last()\
                    .importe
            except AttributeError:
                importe_saldo_anterior = 0
            saldo_cs = cls.crear(
                cuenta=mov.cta_salida,
                importe=importe_saldo_anterior-mov.importe,
                movimiento=mov
            )
            Saldo._actualizar_posteriores(mov.cta_salida, mov, -mov.importe)

            for cta_ancestro in mov.cta_salida.ancestros():
                cls.crear(
                    cuenta=cta_ancestro,
                    movimiento=mov,
                    importe=saldo_cs.importe
                )

        return saldo_ce, saldo_cs

    @classmethod
    def registrar(cls, cuenta, fecha, importe):
        if cuenta is None:
            raise TypeError(
                'Primer argumento debe ser una instancia de la clase Cuenta'
            )

        try:
            # Buscar saldo existente de cuenta en fecha
            saldo = super().tomar(cuenta=cuenta, fecha=fecha)
            saldo.importe += importe
            saldo.save()
        except cls.DoesNotExist:
            # Si no existe, buscar el último saldo anterior
            # para determinar el importe desde el cual partir
            try:
                importe_anterior = cls.tomar(cuenta=cuenta, fecha=fecha).importe
            except cls.DoesNotExist:
                # Si no existe saldo anterior, se parte de cero.
                importe_anterior = 0

            saldo = cls.crear(
                cuenta=cuenta,
                fecha=fecha,
                importe=importe_anterior+importe
            )

        cls._actualizar_posteriores(cuenta, fecha, importe)

        if cuenta.tiene_madre():
            cls.registrar(
                cuenta=cuenta.cta_madre,
                fecha=fecha,
                importe=importe,
            )

        return saldo

    def eliminar(self):
        self.delete()
        Saldo._actualizar_posteriores(
            self.cuenta, self.movimiento, -self.importe)

    @staticmethod
    def _actualizar_posteriores(cuenta, mov, importe):

        # TODO: Refactor. Definir < y > para Movimiento.
        for saldo_post in Saldo.filtro(cuenta=cuenta):
            if saldo_post.movimiento.fecha > mov.fecha or (
                    saldo_post.movimiento.fecha == mov.fecha and
                    saldo_post.movimiento.orden_dia > mov.orden_dia
            ):
                saldo_post.importe += importe
                saldo_post.save()
