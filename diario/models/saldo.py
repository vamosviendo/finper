from django.db import models

from vvmodel.models import MiModel


class Saldo(MiModel):

    cuenta = models.ForeignKey('diario.Cuenta', on_delete=models.CASCADE)
    fecha = models.DateField()
    importe = models.FloatField()

    class Meta:
        unique_together = ['cuenta', 'fecha']
        ordering = ['fecha', 'cuenta']

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

        try:
            saldo = super().tomar(cuenta=cuenta, fecha=fecha)
            saldo.importe += importe
            saldo.save()
        except cls.DoesNotExist:
            saldo_anterior = cls.filtro(cuenta=cuenta, fecha__lt=fecha).last()
            try:
                importe_anterior = saldo_anterior.importe
            except AttributeError:
                importe_anterior = 0
            saldo = cls.crear(
                cuenta=cuenta,
                fecha=fecha,
                importe=importe_anterior+importe
            )

        # Actualizar saldos posteriores de cuenta
        for saldo_post in cls.filtro(cuenta=cuenta, fecha__gt=fecha):
            saldo_post.importe += importe
            saldo_post.save()

        return saldo

    def eliminar(self):
        pass