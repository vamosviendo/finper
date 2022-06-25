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
import operator

from django.db import models

from utils import errors
from vvmodel.models import MiModel

from utils.tiempo import Posicion


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
                posicion=movimiento.posicion,
                cuenta=cuenta
            )

            if result is None:
                raise cls.DoesNotExist

            return result

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
                mov.posicion, cuenta
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
            self.movimiento.posicion,
            self.cuenta
        )

    def anteriores(self):
        return Saldo.anteriores_a(
            self.cuenta,
            self.movimiento.posicion,
        )

    def posteriores(self):
        return Saldo.posteriores_a(
            self.cuenta,
            self.movimiento.posicion,
        )

    def intermedios(self, otro):
        return self.intermedios_con_posicion(otro.movimiento.posicion)

    def intermedios_con_posicion(self, posicion=Posicion(orden_dia=0), inclusive_od=False):
        return Saldo.intermedios_entre_posiciones_de_cuenta(
            cuenta=self.cuenta,
            pos1=self.movimiento.posicion,
            pos2=posicion,
            inclusive_od=inclusive_od
        )
    #
    # def intermedios_con_fecha_y_orden(self, fecha, orden_dia=0,
    #                                   inclusive_od=False):
    #     # TODO: deprecated
    #     return Saldo.intermedios_entre_fechas_y_ordenes_de_cuenta(
    #         cuenta=self.cuenta,
    #         fecha1=self.movimiento.fecha,
    #         fecha2=fecha,
    #         orden_dia1=self.movimiento.orden_dia,
    #         orden_dia2=orden_dia,
    #         inclusive_od=inclusive_od
    #     )

    @staticmethod
    def intermedios_entre_posiciones_de_cuenta(cuenta, pos1, pos2, inclusive_od=False):
        pos_ant, pos_post = sorted([pos1, pos2])
        return Saldo.posteriores_a(
            cuenta, pos_ant, inclusive_od
        ) & Saldo.anteriores_a(
            cuenta, pos_post, inclusive_od
        )
    #
    # @staticmethod
    # def intermedios_entre_fechas_y_ordenes_de_cuenta(
    #         cuenta,
    #         fecha1,
    #         fecha2,
    #         orden_dia1=0,
    #         orden_dia2=0,
    #         inclusive_od=False
    # ):
    #     # TODO: deprecated
    #     (fecha_ant, orden_dia_ant), (fecha_pos, orden_dia_pos) = sorted([
    #         [fecha1, orden_dia1],
    #         [fecha2, orden_dia2]
    #     ])
    #
    #     return Saldo.posteriores_a(
    #         cuenta, Posicion(fecha_ant, orden_dia_ant), inclusive_od
    #     ) & Saldo.anteriores_a(
    #         cuenta, Posicion(fecha_pos, orden_dia_pos), inclusive_od
    #     )

    def sumar_a_este_y_posteriores(self, importe):
        self._actualizar_posteriores(importe)
        self.importe += importe
        self.save()

    @staticmethod
    def _anterior_a(posicion, cuenta):
        return Saldo.anteriores_a(cuenta, posicion).last()

    @staticmethod
    def anteriores_a(cuenta, posicion=Posicion(), inclusive_od=False):
        es_anterior = operator.le if inclusive_od else operator.lt
        ids = [
            saldo.id for saldo in cuenta.saldo_set.all()
            if es_anterior(saldo.movimiento.posicion, posicion)
        ]

        return cuenta.saldo_set.filter(id__in=ids)

    @staticmethod
    def posteriores_a(cuenta, posicion=Posicion(), inclusive_od=False):
        es_posterior = operator.ge if inclusive_od else operator.gt
        ids = [
            saldo.id for saldo in cuenta.saldo_set.all()
            if es_posterior(saldo.movimiento.posicion, posicion)
        ]

        return cuenta.saldo_set.filter(id__in=ids)

    def _actualizar_posteriores(self, importe):
        for saldo_post in self.posteriores():
            saldo_post.importe += importe
            saldo_post.save()
