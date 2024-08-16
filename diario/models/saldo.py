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
from typing import Self, TYPE_CHECKING

from django.db import models

from utils import errors
from vvmodel.models import MiModel

from utils.tiempo import Posicion


if TYPE_CHECKING:
    from diario.models import Movimiento, Cuenta, CuentaInteractiva


class Saldo(MiModel):

    cuenta = models.ForeignKey('diario.Cuenta', on_delete=models.CASCADE)
    movimiento = models.ForeignKey(
        'diario.Movimiento', on_delete=models.CASCADE)
    _importe = models.FloatField()

    class Meta:
        unique_together = ['cuenta', 'movimiento']
        ordering = ['movimiento']

    def __str__(self) -> str:
        return f'{self.cuenta} al {self.movimiento.fecha} - {self.movimiento.orden_dia}: {self.importe}'

    @property
    def importe(self) -> float:
        return self._importe

    @importe.setter
    def importe(self, valor: float):
        self._importe = round(valor, 2)

    @property
    def identidad(self) -> str:
        return f"{self.movimiento.identidad}{self.cuenta.slug}"

    @property
    def posicion(self) -> Posicion:
        return self.movimiento.posicion

    @property
    def viene_de_entrada(self) -> bool:
        try:
            return self == self.movimiento.saldo_ce()
        except AttributeError:
            return False

    @property
    def viene_de_salida(self) -> bool:
        return not self.viene_de_entrada

    @classmethod
    def tomar(cls, **kwargs) -> Self:
        cuenta = kwargs['cuenta']
        movimiento = kwargs['movimiento']

        if cuenta.es_acumulativa:
            try:
                orden_ult_mov = cuenta.movs_directos().last().orden_dia
            except AttributeError:  # No hay movimientos
                orden_ult_mov = -1

            orden_movimiento = f'{movimiento.fecha.strftime("%Y%m%d")}{movimiento.orden_dia}'
            orden_conversion = f'{cuenta.fecha_conversion.strftime("%Y%m%d")}{orden_ult_mov}'

            if orden_movimiento > orden_conversion:
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
    def generar(cls, mov: 'Movimiento', cuenta: 'CuentaInteractiva' = None, salida: bool = False) -> Self:
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

        cotizacion = 1.0 if cuenta.moneda == mov.moneda else mov.cotizacion

        saldo: 'Saldo' = cls.crear(
            cuenta=cuenta,
            importe=importe_saldo_anterior + importe * cotizacion,
            movimiento=mov
        )
        saldo._actualizar_posteriores(importe)

        return saldo

    def eliminar(self):
        self.delete()
        self.cuenta.recalcular_saldos_entre(self.posicion)

    def anterior(self) -> Self:
        return Saldo._anterior_a(
            self.posicion,
            self.cuenta
        )

    def anteriores(self):
        return Saldo.anteriores_a(
            self.cuenta,
            self.posicion,
        )

    def posteriores(self):
        return Saldo.posteriores_a(
            self.cuenta,
            self.posicion,
        )

    @staticmethod
    def _anterior_a(posicion: Posicion, cuenta: models.ForeignKey['Cuenta']) -> 'Saldo':
        return Saldo.anteriores_a(cuenta, posicion).last()

    @staticmethod
    def anteriores_a(
            cuenta: models.ForeignKey['Cuenta'],
            posicion: Posicion = Posicion(),
            inclusive_od: bool = False
    ) -> models.QuerySet['Saldo']:
        es_anterior = operator.le if inclusive_od else operator.lt
        ids = [
            saldo.id for saldo in cuenta.saldo_set.all()
            if es_anterior(saldo.posicion, posicion)
        ]

        return cuenta.saldo_set.filter(id__in=ids)

    @staticmethod
    def posteriores_a(
            cuenta: models.ForeignKey['Cuenta'],
            posicion: Posicion = Posicion(),
            inclusive_od: bool = False
    ) -> models.QuerySet['Saldo']:
        es_posterior = operator.ge if inclusive_od else operator.gt
        ids = [
            saldo.id for saldo in cuenta.saldo_set.all()
            if es_posterior(saldo.posicion, posicion)
        ]

        return cuenta.saldo_set.filter(id__in=ids)

    def _actualizar_posteriores(self, importe: float):
        for saldo_post in self.posteriores():
            saldo_post.importe += importe
            saldo_post.save()
