from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import date

from django.db.models import DateField

if TYPE_CHECKING:
    from diario.models import MiDateField


def hoy():
    return date.today().strftime('%Y-%m-%d')


class Posicion:

    def __init__(self, fecha: date | DateField | MiDateField = None, orden_dia: int = 0):
        self.fecha = fecha
        self.orden_dia = orden_dia

    def __lt__(self, other) -> bool:
        if self.fecha < other.fecha:
            return True
        if self.fecha == other.fecha and self.orden_dia < other.orden_dia:
            return True
        return False

    def __eq__(self, other) -> bool:
        return self.fecha == other.fecha and self.orden_dia == other.orden_dia

    def __le__(self, other) -> bool:
        return self.__lt__(other) or self.__eq__(other)

    def __str__(self) -> str:
        return f'{self.fecha}, {self.orden_dia}'

    def __gt__(self, other) -> bool:
        if self.fecha > other.fecha:
            return True
        if self.fecha == other.fecha and self.orden_dia > other.orden_dia:
            return True
        return False

    def __ge__(self, other) -> bool:
        return self.__gt__(other) or self.__eq__(other)


dia_de_la_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
