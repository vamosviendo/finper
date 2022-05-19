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
        TODO: otra vez, reescribir una vez que terminemos con esto
        Si el movimiento es nuevo (no existía antes, está siendo creado)
        - Generar saldo para cuentas de entrada y/o salida al momento del
          movimiento.
        - Gestionar movimiento entre cuentas de distintos titulares (
          generar, ampliar o cancelar crédito)

        Si el movimiento existía (está siendo modificado)
        - Chequear si cambió alguno de los "campos sensibles" (fecha, importe,
          cta_entrada, cta_salida).
        - Si cambió alguno de estos campos:
          - Eliminar saldo de cuentas de entrada y/o salida del movimiento
            guardado al momento de dicho movimiento, si existen.
          - Generar saldo para cuentas de entrada y/o salida del movimiento
            nuevo al momento del movimiento, si existen.
          TODO: refactor para modificar campos en saldos en vez de
                eliminar/generar
        - Antes de repetir el proceso con la cuenta de salida, actualizarla
          para el caso especial de la división de una cuenta en subcuentas.
          En este caso se crea un movimiento de salida en la cuenta madre
          (todavía interactiva), se convierte la cuenta en acumulativa al
          crear las subcuentas y luego se modifica el movimiento para agregar
          la subcuenta como cuenta de entrada. Es necesario actualizar la
          cuenta de salida para dar cuenta de su conversión en acumulativa.
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
            mov_guardado = self.tomar_de_bd()

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
                    contraparte=mov_guardado
            ):
                # TODO: Probar a nvertir la lógica. Averiguar primero si
                #  mov_guardado tiene ce / cs.

                if self.cta_entrada:
                    if not mov_guardado.cta_entrada:
                        if self.cta_entrada == mov_guardado.cta_salida:
                            saldo = mov_guardado.saldo_cs()
                            saldo._actualizar_posteriores(mov_guardado.importe+self.importe)
                            saldo.importe = saldo.importe + mov_guardado.importe + self.importe
                            saldo.save()
                        else:
                            Saldo.generar(self, salida=False)
                    else:
                        if self.cta_entrada != mov_guardado.cta_entrada:
                            if self.cta_entrada == mov_guardado.cta_salida:
                                saldo = mov_guardado.saldo_cs()
                                saldo._actualizar_posteriores(mov_guardado.importe + self.importe)
                                if self.cta_salida != mov_guardado.cta_entrada:
                                    mov_guardado.saldo_ce().eliminar()
                                saldo.importe = saldo.importe + mov_guardado.importe + self.importe
                                saldo.save()
                            else:
                                if self.cta_salida and self.cta_salida == mov_guardado.cta_entrada:
                                    Saldo.generar(self, salida=False)
                                else:
                                    # TODO
                                    # Esto es muy desprolijo. Tal vez haya que
                                    # rescribir _actualizar_posteriores, o escribir
                                    # un método actualizar_saldos_posteriores en
                                    # Cuenta y usar ese en vez de este.
                                    saldo = mov_guardado.saldo_ce()
                                    saldo._actualizar_posteriores(-self.importe)
                                    saldo.cuenta = self.cta_entrada
                                    saldo._actualizar_posteriores(self.importe)
                                    # TODO: refactorear (se repite en Saldo.generar)
                                    try:
                                        importe_saldo_anterior = Saldo._anterior_a(
                                            self.fecha, self.orden_dia, saldo.cuenta
                                        ).importe
                                    except AttributeError:
                                        importe_saldo_anterior = 0
                                    saldo.importe = importe_saldo_anterior + self.importe
                                    saldo.save()
                        else:
                            # TODO: ¿Se usa esto todavía? Retirar y testear (el if, digo, no el resto)
                            if self.cta_entrada.es_interactiva:
                                saldo = mov_guardado.saldo_ce()
                                saldo.importe = saldo.importe - mov_guardado.importe + self.importe
                                saldo.save()
                                saldo._actualizar_posteriores(self.importe-mov_guardado.importe)
                else:
                    if mov_guardado.cta_entrada \
                            and self.cta_salida != mov_guardado.cta_entrada:
                        mov_guardado.saldo_ce().eliminar()

                if self.cta_salida:
                    if not mov_guardado.cta_salida:
                        if self.cta_salida == mov_guardado.cta_entrada:
                            saldo = mov_guardado.saldo_ce()
                            saldo._actualizar_posteriores(-mov_guardado.importe-self.importe)
                            saldo.importe = saldo.importe - mov_guardado.importe - self.importe
                            saldo.save()
                        else:
                            Saldo.generar(self, salida=True)
                    else:
                        if self.cta_salida != mov_guardado.cta_salida:
                            if self.cta_salida == mov_guardado.cta_entrada:
                                saldo = mov_guardado.saldo_ce()
                                saldo._actualizar_posteriores(-mov_guardado.importe-self.importe)
                                if self.cta_entrada != mov_guardado.cta_salida:
                                    mov_guardado.saldo_cs().eliminar()
                                saldo.importe = saldo.importe - mov_guardado.importe - self.importe
                                saldo.save()
                            else:
                                if self.cta_entrada and self.cta_entrada == mov_guardado.cta_salida:
                                    Saldo.generar(self, salida=True)
                                else:
                                    saldo = mov_guardado.saldo_cs()
                                    saldo._actualizar_posteriores(self.importe)
                                    saldo.cuenta = self.cta_salida
                                    saldo._actualizar_posteriores(-self.importe)
                                    try:
                                        importe_saldo_anterior = Saldo._anterior_a(
                                            self.fecha, self.orden_dia, saldo.cuenta
                                        ).importe
                                    except AttributeError:
                                        importe_saldo_anterior = 0
                                    saldo.importe = importe_saldo_anterior - self.importe
                                    saldo.save()
                        else:
                            if self.cta_salida.es_interactiva:
                                saldo = mov_guardado.saldo_cs()
                                saldo.importe = saldo.importe + mov_guardado.importe - self.importe
                                saldo.save()
                                saldo._actualizar_posteriores(mov_guardado.importe-self.importe)
                else:
                    if mov_guardado.cta_salida \
                            and self.cta_entrada != mov_guardado.cta_salida:
                        mov_guardado.saldo_cs().eliminar()

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
        return (cc1, cc2)

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
