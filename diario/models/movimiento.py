from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django_ordered_field import OrderedCollectionField

from utils import errors
from vvmodel.models import MiModel


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
        movimiento.full_clean()
        movimiento.save(esgratis=esgratis)

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

    def delete(self, *args, **kwargs):
        self.refresh_from_db()
        if self.tiene_cuenta_acumulativa():
            raise errors.ErrorCuentaEsAcumulativa(
                errors.MOVIMIENTO_CON_CA_ELIMINADO)

        if self.cta_entrada:
            self.cta_entrada.saldo -= self.importe
            self.cta_entrada.save()
        if self.cta_salida:
            self.cta_salida.saldo += self.importe
            self.cta_salida.save()

        if self.id_contramov:
            self._eliminar_contramovimiento()

        super().delete(*args, **kwargs)

    def save(self, esgratis=False, *args, **kwargs):

        # Movimiento nuevo
        if self._state.adding:

            if self.cta_entrada:
                self.cta_entrada.saldo += self.importe
                self.cta_entrada.save()
            if self.cta_salida:
                self.cta_salida.saldo -= self.importe
                self.cta_salida.save()

            if self.es_prestamo(esgratis=esgratis):
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
            except AttributeError:
                entradas_iguales = False

            if entradas_iguales:
                try:
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
                    mov_guardado.cta_entrada.saldo -= mov_guardado.importe
                    mov_guardado.cta_entrada.save()

                # Ahora hay una cuenta de entrada
                if self.cta_entrada:
                    self.cta_entrada.saldo += self.importe
                    self.cta_entrada.save()
                self.cta_salida = self.cta_salida.primer_ancestre()\
                    .tomar(slug=self.cta_salida.slug) \
                        if self.cta_salida else None

            # No cambió la cuenta de salida
            try:
                salidas_iguales = self.cta_salida.es_le_misme_que(
                    mov_guardado.cta_salida)
            except AttributeError:
                salidas_iguales = False

            if salidas_iguales:
                try:
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
                    mov_guardado.cta_salida.refresh_from_db()
                    mov_guardado.cta_salida.saldo += mov_guardado.importe
                    mov_guardado.cta_salida.save()
                # Ahora hay una cuenta de salida
                if self.cta_salida:
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

    def es_prestamo(self, esgratis=False):
        return (self.cta_entrada and self.cta_salida and
                self.receptor != self.emisor and
                not esgratis)

    def _cambia_campo(self, *args):
        mov_guardado = self.tomar_de_bd()
        for campo in args:
            if getattr(self, campo) != getattr(mov_guardado, campo):
                return True
        return False

    def _registrar_credito(self):
        self._crear_movimiento_credito()
        self.emisor.deudores.add(self.receptor)

    def _recuperar_cuentas_credito(self, cls):
        return (
            cls.tomar(
                slug=f'_{self.emisor.titname}'
                     f'-{self.receptor.titname}'),
            cls.tomar(
                slug=f'_{self.receptor.titname}'
                     f'-{self.emisor.titname}'))

    def _generar_cuentas_credito(self, cls):
        if not self.emisor or not self.receptor or self.emisor == self.receptor:
            raise errors.ErrorMovimientoNoPrestamo
        return (
            cls.crear(
                nombre=f'Préstamo entre {self.emisor.titname} '
                       f'y {self.receptor.titname}',
                slug=f'_{self.emisor.titname}-{self.receptor.titname}',
                titular=self.emisor
            ),
            cls.crear(
                nombre=f'Préstamo entre {self.receptor.titname} '
                       f'y {self.emisor.titname}',
                slug=f'_{self.receptor.titname}-{self.emisor.titname}',
                titular=self.receptor
            )
        )

    def _crear_movimiento_credito(self):
        from diario.models import Cuenta

        try:
            # TODO: Terminar de reformular esto. Funciona pero es un escracho
            cuenta_acreedora, cuenta_deudora = \
                self._recuperar_cuentas_credito(Cuenta)
            if cuenta_acreedora.saldo >= 0:
                concepto = 'Aumento de crédito'
            elif cuenta_acreedora.saldo < 0:
                concepto = 'Cancelación de crédito' \
                    if self.importe == cuenta_deudora.saldo \
                    else 'Pago a cuenta de crédito'
            else:
                raise ValueError('Error en movimiento de crédito')
        except Cuenta.DoesNotExist:
            cuenta_acreedora, cuenta_deudora = \
                self._generar_cuentas_credito(Cuenta)
            concepto = 'Constitución de crédito'

        contramov = Movimiento.crear(
            concepto=concepto,
            detalle=f'de {self.emisor.nombre} '
                    f'a {self.receptor.nombre}',
            importe=self.importe,
            cta_entrada=cuenta_acreedora,
            cta_salida=cuenta_deudora,
            esgratis=True
        )
        self.id_contramov = contramov.id

    def _eliminar_contramovimiento(self):
        Movimiento.tomar(id=self.id_contramov).delete()
        self.id_contramov = None

    def _regenerar_contramovimiento(self):
        self._eliminar_contramovimiento()
        self._crear_movimiento_credito()


