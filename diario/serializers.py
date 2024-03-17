from vvmodel.serializers import SerializedObject


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
