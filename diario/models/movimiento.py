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
    def sentido(self):
        if self.cta_entrada and self.cta_salida:
            return 't'
        if self.cta_entrada:
            return 'e'
        return 's'

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

    def delete(self, force=False, *args, **kwargs):
        if self.es_automatico and not force:
            raise errors.ErrorMovimientoAutomatico('No se puede eliminar movimiento automático')

        self.refresh_from_db()
        if self.tiene_cuenta_acumulativa():
            raise errors.ErrorCuentaEsAcumulativa(
                errors.MOVIMIENTO_CON_CA_ELIMINADO)

        if self.cta_entrada:
            self.cta_entrada.saldo -= self.importe
            self.cta_entrada.save()

            # TODO: refactor (repetido para cta entrada y salida)
            # Si hay más movimientos en la fecha, retirar importe de saldo
            # Si no hay más movimientos en la fecha, eliminar saldo
            if self.hermanos_de_fecha().count() > 0:
                Saldo.registrar(
                    cuenta=self.cta_entrada,
                    fecha=self.fecha,
                    importe=-self.importe
                )
            else:
                Saldo.tomar(cuenta=self.cta_entrada, fecha=self.fecha).eliminar()

        if self.cta_salida:
            self.cta_salida.saldo += self.importe
            self.cta_salida.save()

            if self.hermanos_de_fecha().count() > 0:
                Saldo.registrar(
                    cuenta=self.cta_salida,
                    fecha=self.fecha,
                    importe=self.importe
                )
            else:
                Saldo.tomar(cuenta=self.cta_salida, fecha=self.fecha).eliminar()

        if self.id_contramov:
            self._eliminar_contramovimiento()

        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        '''
        Si el movimiento es nuevo (no existía antes, está siendo creado)
        - sumar / restar importe de la/s cuenta/s interviniente/s
        - EJECUTAR COMPROBACIONES Y ACCIONES EN REFERENCIA A CUENTAS DE DISTINTOS
          TITULARES (A ser analizadas luego)
        Si el movimiento existía (está siendo modificado)
        - Chequear si cambió la cuenta de entrada.
        - Si no cambió
          - Tratar de sumar importe del movimiento nuevo y restar el del
            movimiento anterior a la cuenta de entrada
        - Si cambió
          - Si antes había una cuenta de entrada, restar el importe del movimiento
            anterior a la cuenta de entrada del movimiento anterior.
          - Si ahora hay una cuenta de entrada, sumar el importe del movimiento
            nuevo a la cuenta de entrada del movimiento nuevo.
        - Antes de repetir el proceso con la cuenta de salida, actualizarla
          por si pasa lo que estamos viendo ahora que pasa

          - Chequear si cambió el importe
          - Si cambió el importe, restar importe anterior y sumar importe nuevo
            a cuenta de entrada

        '''

        # Movimiento nuevo
        if self._state.adding:

            # TODO: convertir esto en método efectos_colaterales, con
            #       métodos menores que manejen cada uno de los efectos:
            #       - modificar_saldos
            #       - registrar_saldos_historicos
            #  def _efectos_colaterales()
            if self.cta_entrada:
                self.cta_entrada.saldo += self.importe
                self.cta_entrada.save()

                Saldo.registrar(
                    cuenta=self.cta_entrada,
                    fecha=self.fecha,
                    importe=self.importe
                )

            if self.cta_salida:
                self.cta_salida.saldo -= self.importe
                self.cta_salida.save()

                Saldo.registrar(
                    cuenta=self.cta_salida,
                    fecha=self.fecha,
                    importe=-self.importe
                )

            if self.es_prestamo():
                if self.receptor not in self.emisor.acreedores.all():
                    self._registrar_credito()
                else:
                    self._crear_movimiento_credito()
                    cuenta_credito = self.receptor.cuentas.get(
                        slug=f'_{self.receptor.titname}'
                             f'-{self.emisor.titname}'
                    )
                    if cuenta_credito.saldo <= 0:
                        self.receptor.cancelar_deuda_de(self.emisor)
                        if cuenta_credito.saldo < 0:
                            self.emisor.deudores.add(self.receptor)

        # Movimiento existente
        else:
            mov_guardado = self.tomar_de_bd()

            if self.es_prestamo():
                if self.id_contramov:
                    if self._cambia_campo(
                            'fecha', 'importe', 'cta_entrada', 'cta_salida'):
                        self._regenerar_contramovimiento()
                else:
                    self._crear_movimiento_credito()
            else:
                if self.id_contramov:
                    self._eliminar_contramovimiento()

            # No cambió la cuenta de entrada
            try:
                entradas_iguales = self.cta_entrada.es_le_misme_que(
                    mov_guardado.cta_entrada)
            except AttributeError:  # no hay cuenta de entrada
                entradas_iguales = False

            if entradas_iguales:
                # Cambió el importe
                try:
                    # Restar de saldo de cuenta de entrada importe antiguo
                    # y sumar el nuevo
                    self.cta_entrada.saldo = self.cta_entrada.saldo \
                                             - mov_guardado.importe \
                                             + self.importe
                    self.cta_entrada.save()
                except AttributeError:
                    pass

            # Cambió la cuenta de entrada
            else:
                # Había una cuenta de entrada
                if mov_guardado.cta_entrada:
                    # Restar importe antiguo de cuenta de entrada antigua
                    mov_guardado.cta_entrada.saldo -= mov_guardado.importe
                    mov_guardado.cta_entrada.save()

                # Ahora hay una cuenta de entrada
                if self.cta_entrada:
                    # Sumar importe nuevo a cuenta de entrada nueva
                    self.cta_entrada.saldo += self.importe
                    self.cta_entrada.save()

                # Refrescar en caso de que la cuenta de salida se haya convertido
                # en acumulativa.
                # Necesario cuando se divide una cuenta en subcuentas convirtiéndola
                # en acumulativa. Los movimientos que pasan el saldo de la cuenta
                # madre a las subcuentas se generan en tres pasos:
                # Primero, se crea un movimiento con la cuenta madre como cta_salida.
                # Luego, se crean las subcuentas y se convierte la cuenta madre
                # en acumulativa.
                # Finalmente, se modifica el movimiento agregándole la subcuenta
                # como cuenta de entrada.
                # En este último paso, es necesario "informarle" al movimiento
                # que su cuenta de salida se ha convertido en acumulativa, para
                # que la trate como tal.
                # Ahora bien, me preguto.
                # ¿Está bien que esta "actualización" se haga acá, en medio del quilombo?
                # ¿No podría estar en algún lugar más relajado?
                # Pasan demasiadas cosas distintas en este save().
                # Todas estas cosas, pelotudo, lo tendrías que haber aclarado en el momento
                # en el que tuviste que agregar estas líneas, y me hubieras
                # ahorrado un montón de trabajo tratando de descularlo.
                # (Me parece que sí tiene que estar acá, al menos por el momento)
                # (Tal vez encapsularlo en un método con un nombre descriptivo)
                self.cta_salida = self.cta_salida.primer_ancestre()\
                    .tomar(slug=self.cta_salida.slug) \
                        if self.cta_salida else None

            # No cambió la cuenta de salida
            try:
                salidas_iguales = self.cta_salida.es_le_misme_que(
                    mov_guardado.cta_salida)
            except AttributeError:  # no hay cuenta de salida
                salidas_iguales = False

            if salidas_iguales:
                # Cambió el importe
                try:
                    # Sumar importe antiguo a cuenta de salida y restar el nuevo
                    self.cta_salida.saldo = self.cta_salida.saldo \
                                            + mov_guardado.importe \
                                            - self.importe
                    self.cta_salida.save()
                except AttributeError:
                    pass

            # Cambió la cuenta de salida
            else:
                # Había una cuenta de salida
                if mov_guardado.cta_salida:
                    # Sumar importe antiguo a cuenta de salida antigua
                    mov_guardado.cta_salida.refresh_from_db()
                    mov_guardado.cta_salida.saldo += mov_guardado.importe
                    mov_guardado.cta_salida.save()
                # Ahora hay una cuenta de salida
                if self.cta_salida:
                    # Restar importe nuevo a cuenta de salida nueva
                    self.cta_salida.saldo -= self.importe
                    self.cta_salida.save()

        super().save(*args, **kwargs)

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

    def es_prestamo(self):
        return (self.cta_entrada and self.cta_salida and
                self.receptor != self.emisor and
                not self.esgratis)

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

    def hermanos_de_fecha(self):
        return Movimiento.filtro(fecha=self.fecha).exclude(pk=self.pk)

    def _cambia_campo(self, *args):
        mov_guardado = self.tomar_de_bd()
        for campo in args:
            if getattr(self, campo) != getattr(mov_guardado, campo):
                return True
        return False

    def _registrar_credito(self):
        self._crear_movimiento_credito()
        self.emisor.deudores.add(self.receptor)

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
        return (cc1, cc2)

    def _crear_movimiento_credito(self):
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

    def _eliminar_contramovimiento(self):
        contramov = Movimiento.tomar(id=self.id_contramov)
        cta1 = contramov.cta_entrada
        tit1 = cta1.titular
        tit2 = contramov.cta_salida.titular
        contramov.delete(force=True)
        cta1.refresh_from_db(fields=['_saldo'])
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