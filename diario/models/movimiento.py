from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple, Optional

from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django_ordered_field import OrderedCollectionField

from vvmodel.models import MiModel
from utils import errors
from utils.tiempo import Posicion
from utils.varios import el_que_no_es

from diario.consts import *
from diario.models.dia import Dia
from diario.models.saldo import Saldo

if TYPE_CHECKING:
    from diario.models import Titular, CuentaInteractiva, Cuenta


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
    dia = models.ForeignKey(Dia, on_delete=models.CASCADE, null=True, blank=True)
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

    cleaner: MovimientoCleaner = None
    viejo: 'Movimiento' = None

    class Meta:
        ordering = ('dia', 'orden_dia')

    def __str__(self):

        string = f'{self.fecha.strftime("%Y-%m-%d")} {self.concepto}: ' \
            f'{self.importe:.2f}'

        if self.cta_entrada:
            string += f' +{self.cta_entrada}'
        if self.cta_salida:
            string += f' -{self.cta_salida}'
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
            return self.cta_salida.titular_original
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
            return self.cta_entrada.titular_original
        except AttributeError:
            return None

    @property
    def posicion(self) -> Posicion:
        return Posicion(fecha=self.fecha, orden_dia=self.orden_dia)

    @property
    def identidad(self) -> str:
        return f"{self.dia.identidad}{self.orden_dia:02d}"

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
        movimiento.full_clean()
        movimiento.save(esgratis=esgratis)

        return movimiento

    @classmethod
    def tomar(cls, **kwargs) -> Movimiento:
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

        if self.cta_entrada:
            self.cta_entrada.saldo_set.get(movimiento=self).eliminar()

        if self.cta_salida:
            self.cta_salida.saldo_set.get(movimiento=self).eliminar()

        super().delete(*args, **kwargs)

        if self.id_contramov:
            self._eliminar_contramovimiento()

    def save(self,
             *args,
             mantiene_orden_dia: bool = False,
             esgratis: bool = False,
             **kwargs):
        """
        Si el movimiento es nuevo (no existía antes, está siendo creado)
        - Generar saldo para cuentas de entrada y/o salida al momento del
          movimiento.
        - Gestionar movimiento entre cuentas de distintos titulares (
          generar, ampliar o cancelar crédito)

        Si el movimiento existía (está siendo modificado)
        - Chequear si cambió alguno de los "campos sensibles" (fecha, importe,
          cta_entrada, cta_salida, moneda).
        - Si cambió alguno de estos campos, actualizar saldos:
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
                Saldo.generar(self, salida=False)
            if self.cta_salida:
                Saldo.generar(self, salida=True)

        else:                    # Movimiento existente
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

            if self.cambia_campo('moneda', contraparte=self.viejo):
                self.importe = self.viejo.importe_en(self.moneda)

            super().save(*args, **kwargs)

            if self.cambia_campo(
                    '_importe', CTA_ENTRADA, CTA_SALIDA, 'dia', 'orden_dia',
                    contraparte=self.viejo
            ):
                for campo_cuenta in campos_cuenta:
                    self._actualizar_saldos_cuenta(campo_cuenta, mantiene_orden_dia)
                self._actualizar_fechas_conversion()

    def refresh_from_db(self, using: str = None, fields: List[str] = None):
        super().refresh_from_db()
        for campo_cuenta in campos_cuenta:
            cuenta = getattr(self, campo_cuenta)
            if cuenta:
                setattr(self, campo_cuenta, cuenta.como_subclase())

    def saldo_ce(self) -> Saldo:
        try:
            return self.cta_entrada.saldo_set.get(movimiento=self)
        except AttributeError:
            raise AttributeError(
                f'Movimiento "{self.concepto}" no tiene cuenta de entrada')

    def saldo_cs(self) -> Saldo:
        try:
            return self.cta_salida.saldo_set.get(movimiento=self)
        except AttributeError:
            raise AttributeError(
                f'Movimiento "{self.concepto}" no tiene cuenta de salida')

    def importe_en(self, otra_moneda):
        return round(self.importe * self.moneda.cotizacion_en(otra_moneda), 2)

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
        return (self.cta_entrada and self.cta_salida and
                self.receptor != self.emisor and
                not self.esgratis)

    def es_anterior_a(self, otro: Movimiento) -> bool:
        return self.posicion < otro.posicion

    def cambia_campo(self, *args, contraparte: Movimiento = None) -> bool:
        mov_guardado = contraparte or self.tomar_de_bd()
        for campo in args:
            if campo not in [x.name for x in self._meta.fields]:
                raise ValueError(f"Campo inexistente: {campo}")
            if getattr(self, campo) != getattr(mov_guardado, campo):
                return True
        return False

    def recuperar_cuentas_credito(self) -> Tuple:
        cls = self.get_related_class(CTA_ENTRADA)
        try:
            return (
                cls.tomar(
                    slug=f'_{self.emisor.titname}'
                         f'-{self.receptor.titname}'),
                cls.tomar(
                    slug=f'_{self.receptor.titname}'
                         f'-{self.emisor.titname}'))
        except cls.DoesNotExist:
            return self._generar_cuentas_credito()

    def as_view_context(self):
        context = {
            'pk': self.pk,
            'identidad': self.identidad,
            'concepto': self.concepto,
            'detalle': self.detalle,
            'fecha': self.fecha,
            'importe': self.importe,
            'es_automatico': self.es_automatico,
        }
        if self.cta_entrada is not None:
            context.update({'cta_entrada': self.cta_entrada.nombre})
        if self.cta_salida is not None:
            context.update({'cta_salida': self.cta_salida.nombre})

        return context

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
        self.cta_salida = self.cta_salida.tomar_del_slug() \
            if self.cta_salida else None
        self.cta_entrada = self.cta_entrada.tomar_del_slug() \
            if self.cta_entrada else None

    def _actualizar_saldos_cuenta(self, campo_cuenta: str, mantiene_orden_dia: bool):
        if campo_cuenta not in campos_cuenta:
            raise ValueError(
                'Argumento incorrecto. Debe ser "cta_entrada"'
                ' o "cta_salida"'
            )
        cuenta = getattr(self, campo_cuenta)
        cuenta_vieja = getattr(self.viejo, campo_cuenta)
        pasa_a_opuesto, viene_de_opuesto, saldo = (
            self._entrada_pasa_a_salida,
            self._salida_pasa_a_entrada,
            self.viejo.saldo_ce,
        ) if campo_cuenta == CTA_ENTRADA else (
            self._salida_pasa_a_entrada,
            self._entrada_pasa_a_salida,
            self.viejo.saldo_cs,
        )

        def cambia_campo(*args) -> bool:
            return self.cambia_campo(*args, contraparte=self.viejo)

        if cuenta is not None:
            if cambia_campo(campo_cuenta):
                if viene_de_opuesto():
                    cuenta.recalcular_saldos_entre(self.posicion)
                else:
                    Saldo.generar(self, salida=(campo_cuenta == CTA_SALIDA))
                self._eliminar_saldo_de_cuenta_vieja_si_existe(cuenta_vieja, pasa_a_opuesto, saldo)

            elif cambia_campo('_importe'):
                cuenta.recalcular_saldos_entre(self.posicion)

            elif getattr(self.viejo, campo_cuenta) is None:
                Saldo.generar(self, salida=(campo_cuenta == CTA_SALIDA))

            if cambia_campo('dia', 'orden_dia'):
                if not mantiene_orden_dia:
                    self._asignar_orden_dia()

                pos_min, pos_max = sorted([self.posicion, self.viejo.posicion])
                cuenta.recalcular_saldos_entre(pos_min, pos_max)
                if cambia_campo(campo_cuenta):
                    cuenta_vieja.recalcular_saldos_entre(pos_min)

        else:
            self._eliminar_saldo_de_cuenta_vieja_si_existe(
                cuenta_vieja, pasa_a_opuesto, saldo)

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
            subcuenta.full_clean()
            subcuenta.save()

    def _asignar_orden_dia(self):
        pos_min, pos_max = sorted([self.posicion, self.viejo.posicion])
        if pos_min.fecha != pos_max.fecha:
            self.orden_dia = 0 \
                if pos_min.fecha == self.viejo.fecha \
                else Movimiento.filtro(dia=Dia.tomar(fecha=pos_min.fecha)).count()
            super().save()

    def _calcular_cotizacion(self):
        if self.cta_entrada is not None and self.cta_salida is not None:
            if self.cta_entrada.moneda != self.cta_salida.moneda:
                if self.cotizacion == 0.0:
                    otra_moneda = el_que_no_es(self.moneda, self.cta_entrada.moneda, self.cta_salida.moneda)
                    self.cotizacion = otra_moneda.cotizacion_en_al(self.moneda, fecha=self.fecha)
            else:
                self.cotizacion = 1.0
        else:
            self.cotizacion = 1.0

    def _eliminar_saldo_de_cuenta_vieja_si_existe(self, cuenta_vieja: Cuenta, pasa_a_opuesto: callable, saldo: callable):
        if cuenta_vieja is not None and not pasa_a_opuesto():
            saldo().eliminar()

    def _cambia_cta_entrada(self) -> bool:
        return (
            self.cta_entrada and self.viejo.cta_entrada
            and self.cta_entrada != self.viejo.cta_entrada
        )

    def _cambia_cta_salida(self) -> bool:
        return (
            self.cta_salida and self.viejo.cta_salida
            and self.cta_salida != self.viejo.cta_salida
        )

    def _salida_pasa_a_entrada(self) -> bool:
        return (
            self.cta_entrada and self.viejo.cta_salida
            and self.cta_entrada == self.viejo.cta_salida
        )

    def _entrada_pasa_a_salida(self) -> bool:
        return (
            self.cta_salida and self.viejo.cta_entrada
            and self.cta_salida == self.viejo.cta_entrada
        )

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
            slug=f'_{self.emisor.titname}-{self.receptor.titname}',
            titular=self.emisor,
            fecha_creacion=self.fecha
        )
        cc2 = cls.crear(
            nombre=f'Deuda de {self.receptor.nombre} '
                   f'con {self.emisor.nombre}',
            slug=f'_{self.receptor.titname}-{self.emisor.titname}',
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
            c.full_clean()
            c.save()

    def _eliminar_contramovimiento(self):
        contramov = Movimiento.tomar(id=self.id_contramov)
        cta1 = contramov.cta_entrada
        tit1 = cta1.titular
        tit2 = contramov.cta_salida.titular
        contramov.delete(force=True)
        self.id_contramov = None
        if cta1.saldo == 0:
            tit2.acreedores.remove(tit1)

    def _regenerar_contramovimiento(self):
        self._eliminar_contramovimiento()
        self._crear_movimiento_credito()

    def _concepto_movimiento_credito(self,
                                     cuenta_emisora: CuentaInteractiva,
                                     cuenta_receptora: CuentaInteractiva) -> str:

        if cuenta_emisora.saldo > 0:  # (1)
            concepto = 'Aumento de crédito'
        elif cuenta_emisora.saldo < 0:
            concepto = 'Cancelación de crédito' if self.importe == cuenta_receptora.saldo \
                else 'Pago en exceso de crédito' if self.importe > cuenta_receptora.saldo \
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
