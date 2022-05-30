from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django_ordered_field import OrderedCollectionField

from utils import errors
from vvmodel.models import MiModel

from diario.models.saldo import Saldo


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


class Movimiento(MiModel):
    fecha = MiDateField(default=date.today)
    orden_dia = OrderedCollectionField(collection='fecha')
    concepto = models.CharField(max_length=120)
    detalle = models.TextField(blank=True, null=True)
    _importe = models.FloatField()
    cta_entrada = models.ForeignKey(
        'diario.Cuenta', related_name='entradas', null=True, blank=True,
        on_delete=models.CASCADE
    )
    cta_salida = models.ForeignKey(
        'diario.Cuenta', related_name='salidas', null=True, blank=True,
        on_delete=models.CASCADE
    )
    id_contramov = models.IntegerField(null=True, blank=True)
    es_automatico = models.BooleanField(default=False)

    viejo = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.esgratis = False

    class Meta:
        ordering = ('fecha', 'orden_dia')

    @property
    def importe(self):
        return self._importe

    @importe.setter
    def importe(self, valor):
        self._importe = round(float(valor), 2)

    @property
    def emisor(self):
        if self.cta_salida:
            return self.cta_salida.titular

    @property
    def receptor(self):
        if self.cta_entrada:
            return self.cta_entrada.titular

    def __str__(self):
        importe = self.importe \
            if self.importe != round(self.importe) \
            else int(self.importe)

        string = \
            f'{self.fecha.strftime("%Y-%m-%d")} {self.concepto}: {importe}'

        if self.cta_entrada:
            string += f' +{self.cta_entrada}'
        if self.cta_salida:
            string += f' -{self.cta_salida}'
        return string

    @classmethod
    def crear(cls, concepto, importe, cta_entrada=None, cta_salida=None,
              esgratis=False, **kwargs):

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
        movimiento.esgratis = esgratis
        movimiento.full_clean()
        movimiento.save()

        return movimiento

    @classmethod
    def tomar(cls, **kwargs):
        mov = super().tomar(**kwargs)
        mov.cta_entrada = mov.cta_entrada.actualizar_subclase() \
            if mov.cta_entrada else None
        mov.cta_salida = mov.cta_salida.actualizar_subclase() \
            if mov.cta_salida else None
        return mov

    def clean(self):

        from_db = self.tomar_de_bd()

        super().clean()

        if self._state.adding:
            # No se admiten movimientos nuevos sobre cuentas acumulativas
            if (self.cta_entrada and self.cta_entrada.es_acumulativa) \
                    or (self.cta_salida and self.cta_salida.es_acumulativa):
                raise errors.ErrorCuentaEsAcumulativa(
                    errors.CUENTA_ACUMULATIVA_EN_MOVIMIENTO)
        else:
            # No se permite modificar movimientos automáticos
            if self.es_automatico and self.any_field_changed():
                raise errors.ErrorMovimientoAutomatico(
                    'No se puede modificar movimiento automático')

        if self.importe == 0:
            raise errors.ErrorImporteCero(
                'Se intentó crear un movimiento con importe cero')

        if not self.cta_entrada and not self.cta_salida:
            raise ValidationError(message=errors.CUENTA_INEXISTENTE)

        if self.cta_entrada == self.cta_salida:
            raise ValidationError(message=errors.CUENTAS_IGUALES)

        if from_db is not None:
            if from_db.tiene_cuenta_acumulativa():
                if self._cambia_campo('importe'):
                    raise errors.ErrorCuentaEsAcumulativa(
                        errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA)

            if from_db.tiene_cta_entrada_acumulativa():
                if self.cta_entrada.slug != from_db.cta_entrada.slug:
                    raise errors.ErrorCuentaEsAcumulativa(
                        errors.CUENTA_ACUMULATIVA_RETIRADA)
                if self.fecha > from_db.cta_entrada.fecha_conversion:
                    raise errors.ErrorCuentaEsAcumulativa(
                        f'{errors.FECHA_POSTERIOR_A_CONVERSION}'
                        f'{from_db.cta_entrada.fecha_conversion}'
                    )

            if from_db.tiene_cta_salida_acumulativa():
                if self.cta_salida.slug != from_db.cta_salida.slug:
                    raise errors.ErrorCuentaEsAcumulativa(
                        errors.CUENTA_ACUMULATIVA_RETIRADA)
                if self.fecha > from_db.cta_salida.fecha_conversion:
                    raise errors.ErrorCuentaEsAcumulativa(
                        f'{errors.FECHA_POSTERIOR_A_CONVERSION}'
                        f'{from_db.cta_salida.fecha_conversion}'
                    )

            if self.tiene_cta_entrada_acumulativa():
                if (from_db.cta_entrada is None
                        or self.cta_entrada.slug != from_db.cta_entrada.slug):
                    raise errors.ErrorCuentaEsAcumulativa(
                        errors.CUENTA_ACUMULATIVA_AGREGADA)

            if self.tiene_cta_salida_acumulativa():
                if (from_db.cta_salida is None
                        or self.cta_salida.slug != from_db.cta_salida.slug):
                    raise errors.ErrorCuentaEsAcumulativa(
                        errors.CUENTA_ACUMULATIVA_AGREGADA)

        if (self.cta_entrada and hasattr(self.cta_entrada, 'fecha_conversion')
                and self.fecha > self.cta_entrada.fecha_conversion):
            raise ValidationError(
                message=errors.CUENTA_ACUMULATIVA_EN_MOVIMIENTO)

        if (self.cta_salida and hasattr(self.cta_salida, 'fecha_conversion')
                and self.fecha > self.cta_salida.fecha_conversion):
            raise ValidationError(
                message=errors.CUENTA_ACUMULATIVA_EN_MOVIMIENTO)

        if self.cta_entrada:
            if self.cta_entrada.es_cuenta_credito:
                if not self.cta_salida:
                    raise ValidationError(
                        'No se permite cuenta crédito en movimiento '
                        'de entrada o salida')
                if not self.cta_salida.es_cuenta_credito:
                    raise ValidationError(
                        'No se permite traspaso '
                        'entre cuenta crédito y cuenta normal')
                if self.cta_salida != self.cta_entrada.contracuenta:
                    raise ValidationError(
                        f'"{self.cta_salida.nombre}" no es la contrapartida '
                        f'de "{self.cta_entrada.nombre}"'
                    )
            if self.fecha < self.cta_entrada.fecha_creacion:
                raise ValidationError(
                    f'Fecha del movimiento ({self.fecha}) es anterior a '
                    f'creación de la cuenta "{self.cta_entrada.nombre}" '
                    f'({self.cta_entrada.fecha_creacion})'
                )

        if self.cta_salida:
            if self.cta_salida.es_cuenta_credito:
                if not self.cta_entrada:
                    raise ValidationError(
                        'No se permite cuenta crédito en movimiento '
                        'de entrada o salida')
                if not self.cta_entrada.es_cuenta_credito:
                    raise ValidationError(
                        'No se permite traspaso '
                        'entre cuenta crédito y cuenta normal')
            if self.fecha < self.cta_salida.fecha_creacion:
                raise ValidationError(
                    f'Fecha del movimiento ({self.fecha}) es anterior a '
                    f'creación de la cuenta "{self.cta_salida.nombre}" '
                    f'({self.cta_salida.fecha_creacion})'
                )

    def delete(self, force=False, *args, **kwargs):
        if self.es_automatico and not force:
            raise errors.ErrorMovimientoAutomatico('No se puede eliminar movimiento automático')

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

    def save(self, *args, **kwargs):
        """
        Si el movimiento es nuevo (no existía antes, está siendo creado)
        - Generar saldo para cuentas de entrada y/o salida al momento del
          movimiento.
        - Gestionar movimiento entre cuentas de distintos titulares (
          generar, ampliar o cancelar crédito)

        Si el movimiento existía (está siendo modificado)
        - Chequear si cambió alguno de los "campos sensibles" (fecha, importe,
          cta_entrada, cta_salida).
        - Si cambió alguno de estos campos, actualizar saldos:
        """

        if self._state.adding:   # Movimiento nuevo

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
                    if self._cambia_campo(
                            'fecha', 'importe', 'cta_entrada', 'cta_salida'):
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
            super().save(*args, **kwargs)

            if self._cambia_campo(
                    'importe', 'cta_entrada', 'cta_salida',
                    contraparte=self.viejo
            ):
                self._actualizar_saldos()

            if self._cambia_campo('fecha', 'orden_dia', contraparte=self.viejo):
                self._actualizar_orden()

    def saldo_ce(self):
        try:
            return self.cta_entrada.saldo_set.get(movimiento=self)
        except AttributeError:
            raise AttributeError(
                f'Movimiento "{self.concepto}" no tiene cuenta de entrada')

    def saldo_cs(self):
        try:
            return self.cta_salida.saldo_set.get(movimiento=self)
        except AttributeError:
            raise AttributeError(
                f'Movimiento "{self.concepto}" no tiene cuenta de salida')

    def tiene_cuenta_acumulativa(self):
        if self.tiene_cta_entrada_acumulativa():
            return True
        if self.tiene_cta_salida_acumulativa():
            return True
        return False

    def tiene_cta_entrada_acumulativa(self):
        return self.cta_entrada and self.cta_entrada.es_acumulativa

    def tiene_cta_salida_acumulativa(self):
        return self.cta_salida and self.cta_salida.es_acumulativa

    def es_prestamo_o_devolucion(self):
        """ Devuelve True si
            - hay cuenta de entrada y cuenta de salida
            - las cuentas de entrada y salida pertenecen a distinto titular
            - el movimiento no se creó como "gratis" (es decir, genera deuda)
        """
        return (self.cta_entrada and self.cta_salida and
                self.receptor != self.emisor and
                not self.esgratis)

    def es_anterior_a(self, otro):
        return self.es_anterior_a_fecha_y_orden(otro.fecha, otro.orden_dia)

    def es_anterior_a_fecha_y_orden(self, fecha, orden_dia=0):
        return (
            self.fecha < fecha
        ) or (
            self.fecha == fecha and self.orden_dia < orden_dia
        )

    def recuperar_cuentas_credito(self):
        cls = self.get_related_class('cta_entrada')
        try:
            return (
                cls.tomar(
                    slug=f'_{self.emisor.titname}'
                         f'-{self.receptor.titname}'),
                cls.tomar(
                    slug=f'_{self.receptor.titname}'
                         f'-{self.emisor.titname}'))
        except cls.DoesNotExist:
            return None, None

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
        self.cta_salida = self.cta_salida.tomar_de_bd() \
            if self.cta_salida else None
        self.cta_entrada = self.cta_entrada.tomar_de_bd() \
            if self.cta_entrada else None

    def _cambia_campo(self, *args, contraparte=None):
        mov_guardado = contraparte or self.tomar_de_bd()
        for campo in args:
            if getattr(self, campo) != getattr(mov_guardado, campo):
                return True
        return False

    def _generar_cuentas_credito(self):
        cls = self.get_related_class('cta_entrada')
        if not self.emisor or not self.receptor or self.emisor == self.receptor:
            raise errors.ErrorMovimientoNoPrestamo
        cc1 = cls.crear(
            nombre=f'Préstamo entre {self.emisor.titname} '
                   f'y {self.receptor.titname}',
            slug=f'_{self.emisor.titname}-{self.receptor.titname}',
            titular=self.emisor
        )
        cc2 = cls.crear(
            nombre=f'Préstamo entre {self.receptor.titname} '
                   f'y {self.emisor.titname}',
            slug=f'_{self.receptor.titname}-{self.emisor.titname}',
            titular=self.receptor,
            contracuenta=cc1
        )
        return cc1, cc2

    def _actualizar_saldos(self):
        """
        - Si la cuenta de entrada es la vieja cuenta de salida, sumar el
          importe del movimiento por dos a la nueva cuenta de entrada.
          - Si ya había una cuenta de entrada y esta no pasó a ser de salida
            (es decir, ya no forma parte del movimiento), eliminar el saldo
            correspondiente.
        - Si la cuenta de entrada es una cuenta que no formaba parte del
          movimiento
          - Generar saldo para la nueva cta_entrada
          - Si había una cta_entrada, eliminar el saldo correspondiente
          - Eliminar saldo de cuentas de entrada y/o salida del movimiento
            guardado al momento de dicho movimiento, si existen.
          - Generar saldo para cuentas de entrada y/o salida del movimiento
            nuevo al momento del movimiento, si existen.
        - Si la cuenta de entrada no cambió, restar importe anterior y sumar
          el nuevo al saldo de la cta_entrada en el movimiento y posteriores.
        - Antes de repetir el proceso con la cuenta de salida, actualizarla
          para el caso especial de la división de una cuenta en subcuentas.
          En este caso se crea un movimiento de salida en la cuenta madre
          (todavía interactiva), se convierte la cuenta en acumulativa al
          crear las subcuentas y luego se modifica el movimiento para agregar
          la subcuenta como cuenta de entrada. Es necesario actualizar la
          cuenta de salida para dar cuenta de su conversión en acumulativa.
        """
        if self.cta_entrada:
            if self._salida_pasa_a_entrada():
                self.viejo.cta_salida.sumar_a_saldo_y_posteriores(
                    self.viejo, self.viejo.importe + self.importe
                )
                if self.viejo.cta_entrada and not self._entrada_pasa_a_salida():
                    self.viejo.saldo_ce().eliminar()

            elif self._cambia_cta_entrada():
                Saldo.generar(self, salida=False)
                if self.viejo.cta_entrada and not self._entrada_pasa_a_salida():
                    self.viejo.saldo_ce().eliminar()

            elif self.viejo.cta_entrada:
                self.viejo.cta_entrada.sumar_a_saldo_y_posteriores(
                    self.viejo, self.importe-self.viejo.importe
                )

            else:   # not mov_viejo.cta_entrada
                Saldo.generar(self, salida=False)

        elif self.viejo.cta_entrada and not self._entrada_pasa_a_salida():
            self.viejo.saldo_ce().eliminar()

        if self.cta_salida:
            if self._entrada_pasa_a_salida():
                self.viejo.cta_entrada.sumar_a_saldo_y_posteriores(
                    self.viejo, -self.viejo.importe - self.importe
                )
                if self.viejo.cta_salida \
                        and not self._salida_pasa_a_entrada():
                    self.viejo.saldo_cs().eliminar()

            elif self._cambia_cta_salida():
                Saldo.generar(self, salida=True)
                if self.viejo.cta_salida and not self._salida_pasa_a_entrada():
                    self.viejo.saldo_cs().eliminar()

            elif self.viejo.cta_salida:
                self.viejo.cta_salida.sumar_a_saldo_y_posteriores(
                    self.viejo, self.viejo.importe - self.importe
                )

            else:
                Saldo.generar(self, salida=True)

        elif self.viejo.cta_salida and not self._salida_pasa_a_entrada():
            self.viejo.saldo_cs().eliminar()

    def _actualizar_orden(self):
        # TODO: saldos_intermedios_de_ctas(
        #           self.viejo.fecha, self.viejo.orden_dia
        #       ) -> intermedios_ce, intermedios_cs
        try:
            intermedios_ce = self.saldo_ce().intermedios_con_fecha_y_orden(
                self.viejo.fecha,
                self.viejo.orden_dia
            )
        except AttributeError:
            intermedios_ce = None
        try:
            intermedios_cs = self.saldo_cs().intermedios_con_fecha_y_orden(
                self.viejo.fecha,
                self.viejo.orden_dia
            )
        except AttributeError:
            intermedios_cs = None

        if self.fecha > self.viejo.fecha:
            # si se cambia la fecha, va a pasar esto. Si se quiere
            # cambiar el orden_dia además de la fecha, hay que hacerlo
            # por separado (cambiar primero la fecha y después el
            # orden_dia)
            self.orden_dia = 0

            if self.cta_entrada:
                saldo_ce = self.saldo_ce()

                # TODO: Saldo.actualizar_saldos(saldos, importe)
                #       (como Saldo.actualizar_posteriores pero actualiza
                #       la lista de saldos que se le pasa y no los posteriores)
                for saldo in intermedios_ce:
                    saldo.importe -= self.importe
                    saldo.save()

                if intermedios_ce.count() > 0:
                    # TODO: self.calcular_nuevo_saldo_dada_ubicacion(entrada)
                    saldo_ce.importe = intermedios_ce.last().importe + self.importe
                    saldo_ce.save()

            if self.cta_salida:
                saldo_cs = self.saldo_cs()

                # TODO: Saldo.actualizar_saldos(saldos, importe)
                for saldo in intermedios_cs:
                    saldo.importe += self.importe
                    saldo.save()

                # TODO: self.calcular_nuevo_saldo_dada_ubicacion(salida)
                #       if intermedios.count() == 0: return
                if intermedios_cs.count() > 0:
                    saldo_cs.importe = intermedios_cs.last().importe - self.importe
                    saldo_cs.save()

        elif self.fecha < self.viejo.fecha:
            self.orden_dia = Movimiento.filtro(fecha=self.fecha).count()

            if self.cta_entrada:
                saldo_ce = self.saldo_ce()

                # TODO: Saldo.actualizar_saldos(saldos, importe)
                for saldo in intermedios_ce:
                    saldo.importe += self.importe
                    saldo.save()

                # TODO: self.calcular_nuevo_saldo_dada_ubicacion(salida)
                #       if intermedios.count() == 0: return
                saldo_ce_anterior = saldo_ce.anterior()
                saldo_ce.importe = saldo_ce_anterior.importe + self.importe \
                    if saldo_ce_anterior \
                    else self.importe
                saldo_ce.save()

            if self.cta_salida:
                saldo_cs = self.saldo_cs()

                # TODO: Saldo.actualizar_saldos(saldos, importe)
                for saldo in intermedios_cs:
                    saldo.importe -= self.importe
                    saldo.save()

                # TODO: self.calcular_nuevo_saldo_dada_ubicacion(salida)
                #       if intermedios.count() == 0: return
                saldo_cs_anterior = saldo_cs.anterior()
                saldo_cs.importe = saldo_cs_anterior.importe - self.importe \
                    if saldo_cs_anterior \
                    else -self.importe
                saldo_cs.save()

        elif self.orden_dia > self.viejo.orden_dia:
            if self.cta_entrada:
                saldo_ce = self.saldo_ce()
                intermedios = self.cta_entrada.saldo_set.filter(
                    movimiento__fecha=self.fecha,
                    movimiento__orden_dia__gte=self.viejo.orden_dia,
                    movimiento__orden_dia__lt=self.orden_dia
                )
                for saldo in intermedios:
                    saldo.importe -= self.importe
                    saldo.save()

                saldo_ce.importe = saldo_ce.anterior().importe + self.importe
                saldo_ce.save()

            if self.cta_salida:
                saldo_cs = self.saldo_cs()
                intermedios = self.cta_salida.saldo_set.filter(
                    movimiento__fecha=self.fecha,
                    movimiento__orden_dia__gte=self.viejo.orden_dia,
                    movimiento__orden_dia__lt=self.orden_dia
                )
                for saldo in intermedios:
                    saldo.importe += self.importe
                    saldo.save()

                saldo_cs.importe = saldo_cs.anterior().importe - self.importe
                saldo_cs.save()


        self.save()

    def _cambia_cta_entrada(self):
        return (
            self.cta_entrada and self.viejo.cta_entrada
            and self.cta_entrada != self.viejo.cta_entrada
        )

    def _cambia_cta_salida(self):
        return (
            self.cta_salida and self.viejo.cta_salida
            and self.cta_salida != self.viejo.cta_salida
        )

    def _salida_pasa_a_entrada(self):
        return (
            self.cta_entrada and self.viejo.cta_salida
            and self.cta_entrada == self.viejo.cta_salida
        )

    def _entrada_pasa_a_salida(self):
        return (
            self.cta_salida and self.viejo.cta_entrada
            and self.cta_salida == self.viejo.cta_entrada
        )

    def _crear_movimiento_credito(self):
        # TODO: ¿manejar con try/except?
        cuenta_acreedora, cuenta_deudora = self.recuperar_cuentas_credito()
        if cuenta_acreedora is None:
            cuenta_acreedora, cuenta_deudora = self._generar_cuentas_credito()

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

    def _gestionar_transferencia(self):
        if self.receptor not in self.emisor.acreedores.all():
            self.emisor.deudores.add(self.receptor)
        else:
            deuda = self.emisor.deuda_con(self.receptor)
            if self.importe >= deuda:
                self.receptor.cancelar_deuda_de(self.emisor)
                if self.importe > deuda:
                    self.emisor.deudores.add(self.receptor)
        self._crear_movimiento_credito()

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

    def _concepto_movimiento_credito(self, cuenta_acreedora, cuenta_deudora):

        if cuenta_acreedora.saldo > 0:  # (1)
            concepto = 'Aumento de crédito'
        elif cuenta_acreedora.saldo < 0:
            concepto = 'Cancelación de crédito' \
                if self.importe == cuenta_deudora.saldo \
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
