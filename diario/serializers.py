from vvmodel.serializers import SerializedObject


class DiaSerializado(SerializedObject):

    @property
    def identidad(self) -> str:
        return self.fields["fecha"].replace("-", "")


class MovimientoSerializado(SerializedObject):

    @property
    def fecha(self):
        return self.fields["dia"]

    @property
    def identidad(self):
        return f"{self.fecha.replace('-', '')}{self.fields['orden_dia']:02d}"


class SaldoSerializado(SerializedObject):

    @property
    def identidad(self) -> str:
        return f"{self.fields['movimiento']}{self.fields['cuenta']}"
