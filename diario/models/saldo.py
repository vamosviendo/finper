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

from utils import errors
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
        return f'{self.cuenta} al {self.movimiento.fecha} - {self.movimiento.orden_dia}: {self.importe}'

    @property
    def importe(self):
        return self._importe

    @importe.setter
    def importe(self, valor):
        self._importe = round(valor, 2)

    @property
    def viene_de_entrada(self):
        try:
            return self == self.movimiento.saldo_ce()
        except AttributeError:
            return False

    @property
    def viene_de_salida(self):
        return not self.viene_de_entrada

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
    def generar(cls, mov, cuenta=None, salida=False):
        importe = mov.importe if not salida else -mov.importe
        cuenta = cuenta or (mov.cta_salida if salida else mov.cta_entrada)
        if cuenta not in (mov.cta_entrada, mov.cta_salida):
            raise errors.ErrorCuentaNoFiguraEnMovimiento(
                f'La cuenta "{cuenta.nombre}" no pertenece al movimiento '
                f'"{mov.concepto}"'
            )

        try:
            importe_saldo_anterior = Saldo._anterior_a(
                mov.fecha, mov.orden_dia, cuenta
            ).importe
        except AttributeError:
            importe_saldo_anterior = 0

        saldo: 'Saldo' = cls.crear(
            cuenta=cuenta,
            importe=importe_saldo_anterior + importe,
            movimiento=mov
        )
        saldo._actualizar_posteriores(importe)

        return saldo

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
        return Saldo.anteriores_a(
            self.movimiento.fecha,
            self.movimiento.orden_dia,
            self.cuenta
        )

    def posteriores(self):
        return Saldo.posteriores_a(
            self.movimiento.fecha,
            self.cuenta,
            self.movimiento.orden_dia,
        )

    def intermedios(self, otro):
        return self.intermedios_con_fecha_y_orden(
            otro.movimiento.fecha,
            otro.movimiento.orden_dia
        )

    def intermedios_con_fecha_y_orden(self, fecha, orden_dia=0,
                                      inclusive_od=False):
        return Saldo.intermedios_entre_fechas_y_ordenes_de_cuenta(
            cuenta=self.cuenta,
            fecha1=self.movimiento.fecha,
            fecha2=fecha,
            orden_dia1=self.movimiento.orden_dia,
            orden_dia2=orden_dia,
            inclusive_od=inclusive_od
        )

    @staticmethod
    def intermedios_entre_fechas_y_ordenes_de_cuenta(
            cuenta,
            fecha1,
            fecha2,
            orden_dia1=0,
            orden_dia2=0,
            inclusive_od=False
    ):
        (fecha_ant, orden_dia_ant), (fecha_pos, orden_dia_pos) = sorted([
            [fecha1, orden_dia1],
            [fecha2, orden_dia2]
        ])

        return Saldo.posteriores_a(
            fecha_ant, cuenta, orden_dia_ant, inclusive_od
        ) & Saldo.anteriores_a(
            fecha_pos, cuenta, orden_dia_pos, inclusive_od
        )

    def sumar_a_este_y_posteriores(self, importe):
        self._actualizar_posteriores(importe)
        self.importe += importe
        self.save()

    @staticmethod
    def _anterior_a(fecha, orden_dia, cuenta):
        return Saldo.anteriores_a(fecha, cuenta, orden_dia).last()

    @staticmethod
    def anteriores_a(fecha, cuenta, orden_dia=0, inclusive_od=False):
        kw_orden_dia = 'movimiento__orden_dia__lte' if inclusive_od \
            else 'movimiento__orden_dia__lt'
        kwarg_orden_dia = {kw_orden_dia: orden_dia}
        return cuenta.saldo_set.filter(
            movimiento__fecha__lt=fecha
        ) | cuenta.saldo_set.filter(
            movimiento__fecha=fecha,
            **kwarg_orden_dia
        )

    @staticmethod
    def posteriores_a(fecha, cuenta, orden_dia=0, inclusive_od=False):
        kw_orden_dia = 'movimiento__orden_dia__gte' if inclusive_od \
            else 'movimiento__orden_dia__gt'
        kwarg_orden_dia = {kw_orden_dia: orden_dia}
        return cuenta.saldo_set.filter(
            movimiento__fecha__gt=fecha
        ) | cuenta.saldo_set.filter(
            movimiento__fecha=fecha,
            **kwarg_orden_dia
        )

    def _actualizar_posteriores(self, importe):
        for saldo_post in self.posteriores():
            saldo_post.importe += importe
            saldo_post.save()

