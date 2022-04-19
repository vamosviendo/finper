"""
Hay un saldo por cuenta y por fecha.
El saldo de la fecha de una cuenta se usa para calcular el saldo al momento
de cada movimiento de la fecha.
"""
from django.db import models

from vvmodel.models import MiModel


class Saldo(MiModel):

    cuenta = models.ForeignKey('diario.Cuenta', on_delete=models.CASCADE)
    fecha = models.DateField()
    importe = models.FloatField()

    class Meta:
        unique_together = ['cuenta', 'fecha']
        ordering = ['fecha', 'cuenta']

    def __str__(self):
        return f'{self.cuenta} al {self.fecha}: {self.importe}'

    @classmethod
    def tomar(cls, **kwargs):
        try:
            return super().tomar(**kwargs)
        except cls.DoesNotExist:
            result = Saldo.filtro(
                cuenta=kwargs['cuenta'],
                fecha__lt=kwargs['fecha']
            ).last()

            if result is None:
                raise cls.DoesNotExist

            return result

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
        Saldo._actualizar_posteriores(self.cuenta, self.fecha, -self.importe)

    @staticmethod
    def _actualizar_posteriores(cuenta, fecha, importe):

        for saldo_post in Saldo.filtro(cuenta=cuenta, fecha__gt=fecha):
            saldo_post.importe += importe
            saldo_post.save()
