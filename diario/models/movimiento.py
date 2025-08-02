from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple, Optional, Self

from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django_ordered_field import OrderedCollectionField

from vvmodel.models import MiModel
from utils import errors
from utils.tiempo import Posicion, str2date
from utils.varios import el_que_no_es

from diario.consts import *
from diario.models.dia import Dia
from diario.models.saldo_diario import SaldoDiario

if TYPE_CHECKING:
    from diario.models import Titular, CuentaInteractiva, Cuenta, Moneda


def es_campo_cuenta_o_none(value: str):
    if value not in (CTA_ENTRADA, CTA_SALIDA, None):
        raise ValidationError(
            f'Valor "{value}" no permitido.'
            f'Valores permitidos: "cta_entrada", "cta_salida" o None'
        )


class MiDateField(models.DateField):
    """ Todavía no entiendo por qué tengo que hacer esto para pasar el
        functional test relacionado con agregar movimiento correctivo.
        Posiblemente tenga que ver con el mocking de datetime.date.
        En algún momento lo averiguaré.
    """

    def to_python(self, value):
        try:
            return super().to_python(value)
        except TypeError:
            return value


class MovimientoManager(models.Manager):
    def get_by_natural_key(self, dia, orden_dia):
        return self.get(dia=dia, orden_dia=orden_dia)


class MovimientoCleaner:

    def __init__(self, mov: Movimiento, viejo: Movimiento):
        self.mov = mov
        self.viejo = viejo

    def no_se_admiten_movimientos_nuevos_sobre_cuentas_acumulativas(self):
        for cuenta in self.mov.cta_entrada, self.mov.cta_salida:
            if cuenta and cuenta.es_acumulativa:
                raise errors.ErrorCuentaEsAcumulativa(
                    errors.CUENTA_ACUMULATIVA_EN_MOVIMIENTO
                )

    def no_se_permite_modificar_movimientos_automaticos(self):
        if self.mov.es_automatico and self.mov.any_field_changed():
            raise errors.ErrorMovimientoAutomatico(
                errors.MODIFICACION_MOVIMIENTO_AUTOMATICO
            )

    def no_se_permiten_movimentos_con_importe_cero(self):
        if self.mov.importe == 0:
            raise errors.ErrorImporteCero(errors.IMPORTE_CERO)

    def debe_haber_al_menos_una_cuenta_y_deben_ser_distintas(self):
        if not self.mov.cta_entrada and not self.mov.cta_salida:
            raise ValidationError(message=errors.CUENTA_INEXISTENTE)
        if self.mov.cta_entrada == self.mov.cta_salida:
            raise ValidationError(message=errors.CUENTAS_IGUALES)

    def no_se_permite_moneda_distinta_de_las_de_cuentas(self):
        monedas_permitidas = set()
        for cuenta in self.mov.cta_entrada, self.mov.cta_salida:
            if cuenta is not None:
                monedas_permitidas.update({cuenta.moneda})

        if self.mov.moneda not in monedas_permitidas:
            if self.mov.cta_entrada:
                monedas = self.mov.cta_entrada.moneda.plural
                if self.mov.cta_salida:
                    monedas += f' o {self.mov.cta_salida.moneda.plural}'
            else:
                monedas = self.mov.cta_salida.moneda.plural
            raise errors.ErrorMonedaNoPermitida(
                message=f'El movimiento debe ser expresado en {monedas}'
            )

    def dia_none_se_reemplaza_por_ultimo_dia(self):
        if self.mov.dia is None:
            try:
                self.mov.dia = Dia.tomar(pk=Dia.ultima_id())
            except AttributeError:
                self.mov.dia = Dia.crear(fecha=date.today())

    def no_se_permite_fecha_anterior_a_creacion_de_cuenta(self):
        for cuenta in self.mov.cta_entrada, self.mov.cta_salida:
            if cuenta is not None and self.mov.fecha < cuenta.fecha_creacion:
                raise errors.ErrorMovimientoAnteriorAFechaCreacion(
                    f'Movimiento "{self.mov.concepto}" anterior a la fecha de creación de '
                    f'la cuenta "{cuenta.nombre}" '
                    f'({self.mov.fecha} < {cuenta.fecha_creacion})')

    def restricciones_con_cuenta_acumulativa(self):
        for campo_cuenta in campos_cuenta:
            cuenta = getattr(self.mov, campo_cuenta)
            cuenta_vieja = getattr(self.viejo, campo_cuenta)
            if cuenta_vieja and cuenta_vieja.es_acumulativa:
                # No se permite cambiar importe de un movimiento con cuenta acumulativa
                if self.mov.cambia_campo('_importe'):
                    raise errors.ErrorCuentaEsAcumulativa(
                        errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA
                    )
                # No se permite cambiar una cuenta acumulativa de un movimiento
                if not cuenta or cuenta.pk != cuenta_vieja.pk:
                    raise errors.ErrorCuentaEsAcumulativa(
                        errors.CUENTA_ACUMULATIVA_RETIRADA
                    )
                # No se admiten movimientos posteriores a conversión de cuenta en acumulativa
                if self.mov.fecha > cuenta_vieja.fecha_conversion and not self.mov.convierte_cuenta:
                    raise errors.ErrorCuentaEsAcumulativa(
                        f'{errors.FECHA_POSTERIOR_A_CONVERSION}'
                        f'{cuenta_vieja.fecha_conversion} '
                        f'(es {self.mov.fecha})'
                    )

            if cuenta and cuenta.es_acumulativa:
                # No se permite cambiar una cuenta del movimiento por una cuenta acumulativa
                cuenta = cuenta.como_subclase()
                if cuenta_vieja is None or cuenta.pk != cuenta_vieja.pk:
                    raise errors.ErrorCuentaEsAcumulativa(
                        errors.CUENTA_ACUMULATIVA_AGREGADA
                    )
                if self.mov.fecha > cuenta.fecha_conversion and not self.mov.convierte_cuenta:
                    raise ValidationError(
                        message=errors.CUENTA_ACUMULATIVA_EN_MOVIMIENTO
                    )

    def restricciones_con_cuenta_credito(self):
        for campo_cuenta in campos_cuenta:
            cuenta = getattr(self.mov, campo_cuenta)
            campo_contracuenta = [x for x in campos_cuenta if x != campo_cuenta][0]
            contracuenta = getattr(self.mov, campo_contracuenta)
            if cuenta and cuenta.es_cuenta_credito:
                if not contracuenta:
                    raise ValidationError(errors.CUENTA_CREDITO_EN_MOV_E_S)
                if not contracuenta.es_cuenta_credito:
                    raise ValidationError(errors.CUENTA_CREDITO_VS_NORMAL)
                if contracuenta != cuenta.contracuenta:
                    raise ValidationError(
                        f'"{contracuenta.nombre}" no es la contrapartida '
                        f'de "{cuenta.nombre}"'
                    )


class Movimiento(MiModel):
    dia = models.ForeignKey(Dia, on_delete=models.CASCADE, null=True, blank=True, related_name="movimiento_set")
    orden_dia = OrderedCollectionField(collection='dia')
    concepto = models.CharField(max_length=120)
    detalle = models.TextField(blank=True, null=True)
    _importe = models.FloatField()
    moneda = models.ForeignKey(     # Determina en qué moneda está expresado el importe del movimiento
        'diario.Moneda', related_name='movimientos', null=True, blank=True,
        on_delete=models.CASCADE
    )
    _cotizacion = models.FloatField(default=0.0)
    cta_entrada = models.ForeignKey(
        'diario.Cuenta', related_name='entradas', null=True, blank=True,
        on_delete=models.CASCADE
    )
    cta_salida = models.ForeignKey(
        'diario.Cuenta', related_name='salidas', null=True, blank=True,
        on_delete=models.CASCADE
    )
    id_contramov = models.IntegerField(null=True, blank=True)
    convierte_cuenta = models.CharField(
        null=True, blank=True, max_length=11,
        validators=[es_campo_cuenta_o_none]
    )
    es_automatico = models.BooleanField(default=False)

    objects = MovimientoManager()
    form_fields = (
        "fecha", "concepto", "detalle", "cotizacion", "importe", "cta_entrada", "cta_salida", "moneda"
    )

    cleaner: MovimientoCleaner = None
    viejo: Self = None

    class Meta:
        ordering = ('dia', 'orden_dia')

    def get_absolute_url(self) -> str:
        return reverse("movimiento", args=[self.pk])

    def get_edit_url(self) -> str:
        return reverse("mov_mod", args=[self.pk])

    def get_delete_url(self) -> str:
        return reverse("mov_elim", args=[self.pk])

    def get_url(self, ente: Titular | Cuenta | None = None):
        try:
            return ente.get_url_with_mov(self)
        except AttributeError:  # ente is None
            return self.get_absolute_url()

    def __str__(self):

        string = f"{self.fecha.strftime("%Y-%m-%d")} {self.orden_dia} {self.concepto} - " \
                 f"{self.cta_salida or '...'} -> {self.cta_entrada or '...'}: "

        if self.es_bimonetario():
            string += f"{self.importe_cta_salida:.2f} {self.cta_salida.moneda.plural} -> " \
                      f"{self.importe_cta_entrada:.2f} {self.cta_entrada.moneda.plural}"
        else:
            string += f"{self.importe:.2f} {self.moneda.plural}"

        return string

    def natural_key(self):
        return self.dia.natural_key() + (self.orden_dia, )

    @property
    def importe(self) -> float:
        return self._importe

    @importe.setter
    def importe(self, valor: float | int):
        self._importe = round(float(valor), 2)

    @property
    def importe_cta_entrada(self) -> float | None:
        try:
            return round(
                self.importe * (
                    1 if self.cta_entrada.moneda == self.moneda
                    else self.cotizacion
                ),
                ndigits=2
            )
        except AttributeError:
            return None

    @property
    def importe_cta_salida(self) -> float | None:
        try:
            return -round(
                self.importe * (
                    1 if self.cta_salida.moneda == self.moneda
                    else self.cotizacion
                ),
                ndigits=2
            )
        except AttributeError:
            return None

    @property
    def fecha(self) -> Optional[date]:
        try:
            return self.dia.fecha
        except AttributeError:
            return None

    @fecha.setter
    def fecha(self, valor: date):
        if valor is not None:
            try:
                self.dia = Dia.tomar(fecha=valor)
            except Dia.DoesNotExist:
                self.dia = Dia.crear(fecha=valor)
        else:
            self.dia = None

    @property
    def emisor(self) -> Optional[Titular]:
        try:
            if self.cta_salida.es_interactiva:
                try:
                    return self.cta_salida.titular
                except AttributeError:
                    return self.cta_salida.como_subclase().titular

            try:
                return self.cta_salida.titular_original
            except AttributeError:
                return self.cta_salida.como_subclase().titular_original

        except AttributeError:
            return None

    @property
    def receptor(self) -> Optional[Titular]:
        try:
            if self.cta_entrada.es_interactiva:
                try:
                    return self.cta_entrada.titular
                except AttributeError:
                    return self.cta_entrada.como_subclase().titular

            try:
                return self.cta_entrada.titular_original
            except AttributeError:
                return self.cta_entrada.como_subclase().titular_original

        except AttributeError:
            return None

    @property
    def posicion(self) -> Posicion:
        return Posicion(fecha=self.fecha, orden_dia=self.orden_dia)

    @property
    def sk(self) -> str:
        return f"{self.dia.sk}{self.orden_dia:02d}"

    @property
    def cotizacion(self) -> float:
        return self._cotizacion

    @cotizacion.setter
    def cotizacion(self, valor: float):
        self._cotizacion = valor

    @classmethod
    def crear(cls,
              concepto: str,
              importe: float | int | str,
              cta_entrada: CuentaInteractiva = None,
              cta_salida: CuentaInteractiva = None,
              esgratis: bool = False,
              **kwargs) -> Movimiento:

        importe = float(importe)

        if importe < 0:
            importe = -importe
            cuenta = cta_salida
            cta_salida = cta_entrada
            cta_entrada = cuenta

        movimiento = cls(
            concepto=concepto,
            importe=importe,
            cta_entrada=cta_entrada,
            cta_salida=cta_salida,
            **kwargs
        )
        movimiento.clean_save(esgratis=esgratis)

        return movimiento

    @classmethod
    def filtro(cls, *args, **kwargs) -> QuerySet[Self]:
        if "fecha" in kwargs.keys():
            kwargs["dia"] = Dia.tomar(fecha=kwargs.pop("fecha"))

        return super().filtro(*args, **kwargs)

    @classmethod
    def tomar(cls, **kwargs) -> Movimiento:
        if "sk" in kwargs.keys():
            kwargs["fecha"] = str2date(kwargs["sk"][:8])
            kwargs["orden_dia"] = kwargs["sk"][8:]
            kwargs.pop("sk")
        if "fecha" in kwargs.keys():
            kwargs["dia"] = Dia.tomar(fecha=kwargs.pop("fecha"))

        mov = super().tomar(**kwargs)

        mov.cta_entrada = mov.cta_entrada.actualizar_subclase() \
            if mov.cta_entrada else None
        mov.cta_salida = mov.cta_salida.actualizar_subclase() \
            if mov.cta_salida else None
        return mov

    def clean(self):
        super().clean()

        cleaning = MovimientoCleaner(self, self.tomar_de_bd())

        cleaning.no_se_permiten_movimentos_con_importe_cero()
        cleaning.debe_haber_al_menos_una_cuenta_y_deben_ser_distintas()

        if self.moneda is None:
            try:
                self.moneda = self.cta_entrada.moneda
            except AttributeError:
                self.moneda = self.cta_salida.moneda

        cleaning.no_se_permite_moneda_distinta_de_las_de_cuentas()
        cleaning.dia_none_se_reemplaza_por_ultimo_dia()
        cleaning.no_se_permite_fecha_anterior_a_creacion_de_cuenta()

        if self._state.adding:
            cleaning.no_se_admiten_movimientos_nuevos_sobre_cuentas_acumulativas()
        else:
            cleaning.no_se_permite_modificar_movimientos_automaticos()
            cleaning.restricciones_con_cuenta_acumulativa()

        cleaning.restricciones_con_cuenta_credito()

    def delete(self, force: bool = False, *args, **kwargs):
        if self.es_automatico and not force:
            raise errors.ErrorMovimientoAutomatico(
                errors.ELIMINACION_MOVIMIENTO_AUTOMATICO
            )

        self.refresh_from_db()

        if self.tiene_cuenta_acumulativa():
            raise errors.ErrorCuentaEsAcumulativa(
                errors.MOVIMIENTO_CON_CA_ELIMINADO)

        for sentido in ("entrada", "salida"):
            cuenta = getattr(self, f"cta_{sentido}")
            if cuenta is not None:
                saldo_diario = cuenta.saldodiario_set.get(dia=self.dia)
                if cuenta.movs_en_fecha(self.dia).count() == 1:
                    saldo_diario.eliminar()
                else:
                    saldo_diario.importe -= self.importe_cta(sentido)
                    saldo_diario.clean_save()

        super().delete(*args, **kwargs)

        if self.id_contramov:
            self._eliminar_contramovimiento()

    def clean_save(
            self, exclude=None, validate_unique=True, validate_constraints=True,
            force_insert=False, force_update=False, using=None, update_fields=None,
            mantiene_orden_dia: bool = False, esgratis: bool = False
    ):
        super().full_clean()
        self.save(
            force_insert, force_update, using, update_fields,
            mantiene_orden_dia=mantiene_orden_dia, esgratis=esgratis)

    def save(self,
             *args,
             mantiene_orden_dia: bool = False,
             esgratis: bool = False,
             **kwargs):
        """
        TODO: Revisar y actualizar este comentario
        Si el movimiento es nuevo (no existía antes, está siendo creado)
        - Calcular saldo diario para cuentas de entrada y/o salida al momento del
          movimiento.
        - Gestionar movimiento entre cuentas de distintos titulares (
          generar, ampliar o cancelar crédito)

        Si el movimiento existía (está siendo modificado)
        - Chequear si cambió alguno de los "campos sensibles" (fecha, importe,
          cta_entrada, cta_salida, moneda, cotización).
        - Si cambió alguno de estos campos, actualizar saldos diarios:
        """
        if self._state.adding:   # Movimiento nuevo

            self._calcular_cotizacion()

            # TODO extract Movimiento.__setup__()
            if not hasattr(self, 'esgratis'):
                self.esgratis = esgratis

            if self.es_prestamo_o_devolucion():
                self._gestionar_transferencia()

            super().save(*args, **kwargs)
            if self.cta_entrada:
                SaldoDiario.calcular(self, "entrada")
            if self.cta_salida:
                SaldoDiario.calcular(self, "salida")

        else:  # Movimiento existente
            self.viejo = self.tomar_de_bd()

            if self.es_prestamo_o_devolucion():
                # El mov es una transacción no gratuita entre titulares
                if self.id_contramov:
                    # El movimiento ya era una transacción no gratuita entre
                    # titulares
                    if self.cambia_campo(
                            'dia', '_importe', CTA_ENTRADA, CTA_SALIDA):
                        self._regenerar_contramovimiento()
                else:
                    # El movimiento no era una transacción no gratuita entre
                    # titulares y ahora lo es
                    self._crear_movimiento_credito()
            else:
                # El movimiento no es una transacción no gratuita entre
                # titulares
                if self.id_contramov:
                    # El movimiento era una transacción no gratuita entre
                    # titulares y ahora ya no
                    self._eliminar_contramovimiento()

            self._actualizar_cuenta_convertida_en_acumulativa()

            if self._hay_que_recalcular_cotizacion():
                self._recalcular_cotizacion()
            if self._hay_que_recalcular_importe():
                self._recalcular_importe()

            self._recalcular_saldos_diarios()

            if self.cambia_campo('dia'):
                self._actualizar_orden_dia()

            super().save(*args, **kwargs)

            if self.cambia_campo(
                    '_importe', '_cotizacion', CTA_ENTRADA, CTA_SALIDA, 'dia', 'orden_dia',
                    contraparte=self.viejo
            ):
                self._actualizar_fechas_conversion()

    def refresh_from_db(self, using: str = None, fields: List[str] = None):
        super().refresh_from_db()
        for campo_cuenta in campos_cuenta:
            cuenta = getattr(self, campo_cuenta)
            if cuenta:
                setattr(self, campo_cuenta, cuenta.como_subclase())

    def importe_en(self, otra_moneda: Moneda, compra: bool = False) -> float:
        return round(self.importe * self.moneda.cotizacion_en(otra_moneda, compra), 2)

    def importe_cta(self, sentido: str) -> float:
        try:
            return getattr(self, f"importe_cta_{sentido}")
        except AttributeError:
            raise ValueError('Los valores permitidos son "entrada" y "salida"')

    def tiene_cuenta_acumulativa(self) -> bool:
        if self.tiene_cta_entrada_acumulativa():
            return True
        if self.tiene_cta_salida_acumulativa():
            return True
        return False

    def tiene_cta_entrada_acumulativa(self) -> bool:
        return self.cta_entrada and self.cta_entrada.es_acumulativa

    def tiene_cta_salida_acumulativa(self) -> bool:
        return self.cta_salida and self.cta_salida.es_acumulativa

    def es_prestamo_o_devolucion(self) -> bool:
        """ Devuelve True si
            - hay cuenta de entrada y cuenta de salida
            - las cuentas de entrada y salida pertenecen a distinto titular
            - el movimiento no se creó como "gratis" (es decir, genera deuda)
        """
        try:
            esgratis = self.esgratis
        except AttributeError:
            esgratis = self.id_contramov is None

        return (self.cta_entrada and self.cta_salida and
                self.receptor != self.emisor and
                not esgratis)

    def es_bimonetario(self) -> bool:
        if (self.cta_entrada and self.cta_salida) and (self.cta_entrada.moneda != self.cta_salida.moneda):
            return True
        return False

    def es_anterior_a(self, otro: Movimiento) -> bool:
        return self.posicion < otro.posicion

    def cambia_campo(self, *args, contraparte: Movimiento = None) -> bool:
        mov_guardado = contraparte or self.tomar_de_bd()
        for campo in args:
            if campo not in [x.name for x in self._meta.fields]:
                raise ValueError(f"Campo inexistente: {campo}")
            try:
                if getattr(self, campo) != getattr(mov_guardado, campo):
                    return True
            except AttributeError:  # mov_guardado == None => El movimiento es nuevo.
                return True
        return False

    def cambia_cuenta_por_cuenta_en_otra_moneda(self, moneda_del_movimiento: bool = True) -> bool:
        """ Devuelve true si alguna de las cuentas cambia por una cuenta en otra moneda.
            Si moneda_del_movimiento es True, verifica la cuenta en moneda del movimiento.
            Si moneda_del_movimiento es False, verifica la cuenta en moneda distinta a la del movimiento.
        """
        viejo = self.tomar_de_bd() or self.viejo
        for campo_cuenta in campos_cuenta:
            if self.cambia_campo(campo_cuenta, contraparte=viejo):
                cuenta = getattr(self, campo_cuenta)
                try:
                    cuenta_vieja = getattr(viejo, campo_cuenta)
                    contracuenta_vieja = getattr(viejo, CTA_ENTRADA if campo_cuenta == CTA_SALIDA else CTA_SALIDA)
                except AttributeError:  # viejo == None => El movimiento es nuevo.
                    return True

                try:
                    moneda = cuenta.moneda
                    moneda_vieja = cuenta_vieja.moneda
                # cuenta == None o cuenta_vieja == None => El movimiento viejo o el nuevo son de entrada o salida
                except AttributeError:
                    return True
                if moneda != moneda_vieja:
                    if not moneda_del_movimiento and contracuenta_vieja.moneda == viejo.moneda:
                        return True
                    if moneda_del_movimiento and cuenta_vieja.moneda == viejo.moneda:
                        return True

        return False

    def recuperar_cuentas_credito(self) -> Tuple:
        cls = self.get_related_class(CTA_ENTRADA)
        sk_emisor = self.emisor.sk
        sk_receptor = self.receptor.sk
        try:
            return (
                cls.tomar(
                    sk=f'_{sk_emisor}'
                         f'-{sk_receptor}'),
                cls.tomar(
                    sk=f'_{sk_receptor}'
                         f'-{sk_emisor}'))
        except cls.DoesNotExist:
            return self._generar_cuentas_credito()

    # Métodos protegidos

    def _actualizar_cuenta_convertida_en_acumulativa(self):
        """ Este paso es necesario para el caso en el que se divide una cuenta
            en subcuentas convirtiéndola en acumulativa (ver
            diario.models.cuenta.CuentaInteractiva.dividir_entre().
            Para pasar el saldo de la cuenta madre a las subcuentas se crean
            movimientos, los cuales se generan en tres pasos:
            - por cada subcuenta se crea un movimiento con la cuenta madre
              como cuenta de salida o entrada, según el signo de su saldo
            - se crean las subcuentas y se convierte la cuenta madre en
              acumulativa
            - se modifican los movimientos recién creados agregándole la
              subcuenta como cuenta de entrada o salida.
            En este último paso, es necesario "informarle" al movimiento que
            su cuenta de salida/entrada se ha convertido en acumulativa, para que la
            trate como tal.
        """
        self.cta_salida = self.cta_salida.tomar_del_sk() \
            if self.cta_salida else None
        self.cta_entrada = self.cta_entrada.tomar_del_sk() \
            if self.cta_entrada else None

    def _recalcular_saldos_diarios(self):
        for campo_cuenta in campos_cuenta:
            if self.cambia_campo(campo_cuenta, "dia", "_importe", "_cotizacion"):
                cta_nueva = getattr(self, campo_cuenta)
                cta_vieja = getattr(self.viejo, campo_cuenta)

                if cta_vieja is not None:
                    saldo_cta_vieja = SaldoDiario.tomar(cuenta=cta_vieja, dia=self.viejo.dia)
                    movs_dia_cta_vieja = cta_vieja.movs().filter(dia=self.viejo.dia)
                    campo_opuesto = el_que_no_es(campo_cuenta, *campos_cuenta)
                    cta_nueva_opuesta = getattr(self, campo_opuesto)

                    if movs_dia_cta_vieja.count() < 2 and cta_vieja not in (cta_nueva, cta_nueva_opuesta):
                        saldo_cta_vieja.eliminar()
                    else:
                        saldo_cta_vieja.importe -= getattr(self.viejo, f"importe_{campo_cuenta}")
                        saldo_cta_vieja.clean_save()

                if cta_nueva is not None:
                    SaldoDiario.calcular(self, campo_cuenta)

    def _actualizar_fechas_conversion(self):
        if self.cambia_campo('dia', contraparte=self.viejo) and self.convierte_cuenta:
            cuenta = self.cta_entrada \
                if self.convierte_cuenta == CTA_SALIDA \
                else self.cta_salida
            subcuenta = self.cta_salida if cuenta == self.cta_entrada else self.cta_entrada

            cuenta.fecha_conversion = subcuenta.fecha_creacion = self.fecha
            # Se omite cuenta.full_clean() para evitar error de fecha de
            # conversión posterior a fecha de creación de subcuentas
            cuenta.save()
            subcuenta.clean_save()

    def _actualizar_orden_dia(self):
        if self.dia.fecha > self.viejo.dia.fecha:
            self.orden_dia = 0
        else:
            self.orden_dia = self.dia.movimientos.count()

    def _hay_que_recalcular_cotizacion(self) -> bool:
        """ Si cambia la moneda del movimiento, se recalcula la cotización
            del movimiento en base a las nuevas monedas.
            Si una cuenta cambia por una cuenta en otra moneda, ídem.
            Devuelve True si se recalculó la cotización
        """
        # Si se cambia manualmente la cotización, no se la recalcula
        if self.cambia_campo('_cotizacion', contraparte=self.viejo):
            return False

        # Si cambia moneda, se recalcula cotización
        if self.moneda != self.viejo.moneda:
            return True

        for campo_cuenta in campos_cuenta:
            cuenta = getattr(self, campo_cuenta)
            campo_contracuenta = el_que_no_es(campo_cuenta, "cta_entrada", "cta_salida")
            contracuenta_vieja = getattr(self.viejo, campo_contracuenta)
            contracuenta = getattr(self, campo_contracuenta)

            # Si el movimiento no es un traspaso, no se recalcula cotización
            if cuenta is None or contracuenta is None:
                return False

            # Si a un movimiento de e/s se le agrega una contracuenta en otra moneda, se recalcula cotización
            if contracuenta_vieja is None and contracuenta is not None and contracuenta.moneda != cuenta.moneda:
                return True

        # Si cambia cuenta por cuenta en otra moneda y no se cambia manualmente la cotización,
        # se la recalcula.
        if self.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) \
                and not self.cambia_campo("_cotizacion", contraparte=self.viejo):
            return True

        return False

    def _hay_que_recalcular_importe(self) -> bool:
        # Si se cambia manualmente el importe, no se lo recalcula
        if self.cambia_campo('_importe', contraparte=self.viejo):
            return False

        if self.cambia_campo('moneda', contraparte=self.viejo):
            # TODO: Este condicional habría que revisarlo y reformularlo en algún momento con una lógica más clara
            try:
                moneda_cta_entrada = self.viejo.cta_entrada.moneda
                moneda_cta_salida = self.viejo.cta_salida.moneda
            except AttributeError:  # cta_entrada o cta_salida del movimiento viejo es None
                return True

            if self.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=True) and \
                    self.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False) and \
                    moneda_cta_entrada != moneda_cta_salida:
                return False
            return True

        if self.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=True):
            if self.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=False):
                return False
            return True

        return False

    def _calcular_cotizacion(self, cambia_moneda: bool = False):
        if self.cta_entrada is not None and self.cta_salida is not None:
            if self.cta_entrada.moneda != self.cta_salida.moneda:
                if self.cotizacion == 0.0 or cambia_moneda:
                    otra_moneda = el_que_no_es(self.moneda, self.cta_entrada.moneda, self.cta_salida.moneda)
                    if self.cambia_cuenta_por_cuenta_en_otra_moneda(True) or self.cambia_cuenta_por_cuenta_en_otra_moneda(False):
                        self.cotizacion = self.moneda.cotizacion_en_al(
                            otra_moneda,
                            fecha=self.fecha,
                            compra=self.cta_entrada.moneda == self.moneda
                        )
                    else:
                        self.cotizacion = 1 / self.cotizacion
            else:
                self.cotizacion = 1.0
        else:
            self.cotizacion = 1.0

    def _recalcular_cotizacion(self):
        self._calcular_cotizacion(cambia_moneda=True)

    def _recalcular_importe(self):
        if self.cambia_campo(
                "moneda", contraparte=self.viejo
        ) and not self.cambia_cuenta_por_cuenta_en_otra_moneda(moneda_del_movimiento=True):
            self.importe = round(self.viejo.importe / self.cotizacion, 2)
        else:
            self.importe = round(self.viejo.importe * self.viejo.cotizacion / self.cotizacion, 2)

    def _gestionar_transferencia(self):
        if self.receptor not in self.emisor.acreedores.all():
            self.emisor.deudores.add(self.receptor)
        else:
            deuda = self.emisor.deuda_con(self.receptor)
            if self.importe >= deuda:
                self.receptor.cancelar_deuda_de(self.emisor)
                if self.importe > deuda:
                    self.emisor.deudores.add(self.receptor)
                    self._regenerar_nombres_de_cuentas_credito()
        self._crear_movimiento_credito()

    def _crear_movimiento_credito(self):
        cuenta_acreedora, cuenta_deudora = self.recuperar_cuentas_credito()

        concepto = self._concepto_movimiento_credito(
            cuenta_acreedora, cuenta_deudora)

        contramov = Movimiento.crear(
            fecha=self.fecha,
            concepto=concepto,
            detalle=f'de {self.emisor.nombre} '
                    f'a {self.receptor.nombre}',
            importe=self.importe,
            cta_entrada=cuenta_acreedora,
            cta_salida=cuenta_deudora,
            es_automatico=True,
            esgratis=True
        )
        self.id_contramov = contramov.id

    def _generar_cuentas_credito(self) -> Tuple:
        cls = self.get_related_class(CTA_ENTRADA)
        if not self.emisor or not self.receptor or self.emisor == self.receptor:
            raise errors.ErrorMovimientoNoPrestamo
        cc1 = cls.crear(
            nombre=f'Préstamo de {self.emisor.nombre} '
                   f'a {self.receptor.nombre}',
            sk=f'_{self.emisor.sk}-{self.receptor.sk}',
            titular=self.emisor,
            fecha_creacion=self.fecha
        )
        cc2 = cls.crear(
            nombre=f'Deuda de {self.receptor.nombre} '
                   f'con {self.emisor.nombre}',
            sk=f'_{self.receptor.sk}-{self.emisor.sk}',
            titular=self.receptor,
            _contracuenta=cc1,
            fecha_creacion=self.fecha
        )
        return cc1, cc2

    def _regenerar_nombres_de_cuentas_credito(self):
        ce = self.emisor.cuenta_credito_con(self.receptor)
        cs = self.receptor.cuenta_credito_con(self.emisor)
        ce.nombre = f'Préstamo de {self.emisor.nombre} a {self.receptor.nombre}'
        cs.nombre = f'Deuda de {self.receptor.nombre} con {self.emisor.nombre}'
        for c in ce, cs:
            c.clean_save()

    def _eliminar_contramovimiento(self):
        contramov = Movimiento.tomar(id=self.id_contramov)
        cta1 = contramov.cta_entrada
        tit1 = cta1.titular
        tit2 = contramov.cta_salida.titular
        contramov.delete(force=True)
        self.id_contramov = None
        if cta1.saldo() == 0:
            tit2.acreedores.remove(tit1)

    def _regenerar_contramovimiento(self):
        self._eliminar_contramovimiento()
        self._crear_movimiento_credito()

    def _concepto_movimiento_credito(self,
                                     cuenta_emisora: CuentaInteractiva,
                                     cuenta_receptora: CuentaInteractiva) -> str:

        if cuenta_emisora.saldo() > 0:  # (1)
            concepto = 'Aumento de crédito'
        elif cuenta_emisora.saldo() < 0:
            concepto = 'Cancelación de crédito' if self.importe == cuenta_receptora.saldo() \
                else 'Pago en exceso de crédito' if self.importe > cuenta_receptora.saldo() \
                else 'Pago a cuenta de crédito'
        else:
            concepto = 'Constitución de crédito'

        return concepto

'''
(1) cuenta_acreedora y cuenta_deudora lo son con respecto al movimiento, no en
    esencia. cuenta_acreedora es la cuenta del que entrega el dinero y 
    cuenta_deudora la del que lo recibe. cuenta_acreedora puede pertenecer a un
    deudor, y su saldo en ese caso será negativo.
'''
