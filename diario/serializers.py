from vvmodel.serializers import SerializedObject


class CuentaSerializada(SerializedObject):
    @classmethod
    def model_string(cls) -> str:
        return "diario.cuenta"

    def campos_polimorficos(self) -> dict:
        try:
            elemento = self.container.tomar(model="diario.cuentainteractiva", pk=self.pk)
        except StopIteration:
            elemento = self.container.tomar(model="diario.cuentaacumulativa", pk=self.pk)
        return elemento.fields

    def titname(self) -> str:
        campos = self.campos_polimorficos()
        try:
            titular = campos["titular"]
        except KeyError:
            titular = campos["titular_original"]
        return titular[0]

    def es_cuenta_credito(self) -> bool:
        cuentas_interactivas = self.container.filter_by_model("diario.cuentainteractiva")
        contracuentas = [
            x.fields["_contracuenta"][0] if x.fields["_contracuenta"] else None
            for x in cuentas_interactivas
        ]
        return self.fields["slug"] in contracuentas or (
            self.campos_polimorficos().get("_contracuenta") is not None
        )


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
        return self.fields["dia"][0]

    @property
    def identidad(self) -> str:
        return f"{self.fecha.replace('-', '')}{self.fields['orden_dia']:02d}"


class SaldoSerializado(SerializedObject):
    @classmethod
    def model_string(cls) -> str:
        return "diario.saldo"

    @property
    def identidad(self) -> str:
        return f"{self.fields['movimiento'][0].replace('-', '')}" \
               f"{self.fields['movimiento'][1]:02d}" \
               f"{self.fields['cuenta'][0]}"
