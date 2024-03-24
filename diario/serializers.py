from typing import Self

from vvmodel.serializers import SerializedObject, SerializedDb


class DiaSerializado(SerializedObject):
    @classmethod
    def model_string(cls) -> str:
        return "diario.dia"

    @property
    def identidad(self) -> str:
        return self.fields["fecha"].replace("-", "")


class MovimientoSerializado(SerializedObject):
    @classmethod
    def model_string(cls) -> str:
        return "diario.movimiento"

    @property
    def fecha(self) -> str:
        return self.fields["dia"]

    @property
    def identidad(self) -> str:
        return f"{self.fecha.replace('-', '')}{self.fields['orden_dia']:02d}"


class SaldoSerializado(SerializedObject):
    @classmethod
    def model_string(cls) -> str:
        return "diario.saldo"

    @property
    def identidad(self) -> str:
        return f"{self.fields['movimiento']}{self.fields['cuenta']}"
