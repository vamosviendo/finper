import sys, inspect

from typing import Self

from vvmodel.serializers import SerializedObject


def get_class_tuples() -> list[tuple[str, type]]:
    return [x for x in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(x[1])]

def get_serializers() -> list[type]:
    return [x[1] for x in get_class_tuples() if issubclass(x[1], SerializedObject)]

def get_serializer(name: str) -> type:
    serializers = get_class_tuples()
    return next(x for x in serializers if x[0] == name)[1]


class SkSimpleMixin:
    fields: dict

    @property
    def sk(self) -> str:
        return self.fields["_sk"]

    @sk.setter
    def sk(self, value: str):
        self.fields["_sk"] = value


class CuentaSerializada(SerializedObject, SkSimpleMixin):
    @classmethod
    def model_string(cls) -> str:
        return "diario.cuenta"

    def campos_polimorficos(self) -> dict:
        try:
            elemento = self.container.tomar(model="diario.cuentainteractiva", pk=self.pk)
        except StopIteration:
            elemento = self.container.tomar(model="diario.cuentaacumulativa", pk=self.pk)
        return elemento.fields

    def sk_tit(self) -> str:
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
        return self.sk in contracuentas or (
            self.campos_polimorficos().get("_contracuenta") is not None
        )

    def es_cuenta_independiente(self) -> bool:
        """ Devuelve True si la cuenta no depende de una cuenta madre ni es
            una cuenta crédito"""
        return \
            self in self.container.filtrar(cta_madre=None) \
            and not self.es_cuenta_credito()

    def es_acumulativa(self) -> bool:
        return self.pk in [x.pk for x in self.container.filter_by_model("diario.cuentaacumulativa")]

    def es_subcuenta_de(self, otra: Self):
        return self.fields["cta_madre"] == [otra.sk]

class DiaSerializado(SerializedObject):
    @classmethod
    def model_string(cls) -> str:
        return "diario.dia"

    @property
    def sk(self) -> str:
        return self.fields["fecha"].replace("-", "")


class MovimientoSerializado(SerializedObject):
    @classmethod
    def model_string(cls) -> str:
        return "diario.movimiento"

    @property
    def fecha(self) -> str:
        return self.fields["dia"][0]

    @property
    def sk(self) -> str:
        return f"{self.fecha.replace('-', '')}{self.fields['orden_dia']:02d}"

    def involucra_cuenta(self, cuenta: CuentaSerializada) -> bool:
        return [cuenta.sk] in (self.fields["cta_entrada"], self.fields["cta_salida"])

    def es_entrada_o_salida(self):
        return self.fields["cta_entrada"] is None or self.fields["cta_salida"] is None


class SaldoDiarioSerializado(SerializedObject):
    @classmethod
    def model_string(cls) -> str:
        return "diario.saldodiario"

    @property
    def sk(self) -> str:
        return f"{self.fields['dia'][0].replace('-', '')}" \
               f"{self.fields['cuenta'][0]}"


class MonedaSerializada(SerializedObject, SkSimpleMixin):
    @classmethod
    def model_string(cls) -> str:
        return "diario.moneda"


class TitularSerializado(SerializedObject, SkSimpleMixin):
    @classmethod
    def model_string(cls) -> str:
        return "diario.titular"


class CotizacionSerializada(SerializedObject):
    @classmethod
    def model_string(cls) -> str:
        return "diario.cotizacion"

    @property
    def sk(self) -> str:
        return self.fields["fecha"].replace("-", "") + self.fields["moneda"][0]
