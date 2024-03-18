from vvmodel.serializers import SerializedObject


class DiaSerializado(SerializedObject):

    @property
    def identidad(self) -> str:
        return self.fields["fecha"].replace("-", "")


class MovimientoSerializado(SerializedObject):

    @property
    def fecha(self):
        try:
            dias = [x for x in self.container if x.model == "diario.dia"]
        except TypeError:    # container is None
            dias = []
        return next(
            (x.fields['fecha'] for x in dias if x.pk == self.fields['dia']),
            None
        )

    @property
    def identidad(self):
        return f"{self.fecha.replace('-', '')}{self.fields['orden_dia']:02d}"


class SaldoSerializado(SerializedObject):

    @property
    def identidad(self) -> str:
        id_movimiento = next(
            MovimientoSerializado(x).identidad for x in self.container
            if x.model == "diario.movimiento" and x.pk == self.fields["movimiento"]
        )
        slug_cuenta = next(
            x.fields["slug"] for x in self.container
            if x.model == "diario.cuenta" and x.pk == self.fields["cuenta"]
        )
        return f"{id_movimiento}{slug_cuenta}"
