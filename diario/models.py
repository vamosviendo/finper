from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Sum

from utils import errors
from utils.clases.mimodel import MiModel
from utils.errors import ErrorOpciones


def hoy():
    return date.today()


alfaminusculas = RegexValidator(
    r'^[0-9a-z]*$', 'Solamente caracteres alfanuméricos')


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


class Cuenta(MiModel):
    nombre = models.CharField(max_length=50, unique=True)
    slug = models.CharField(
        max_length=4, unique=True, validators=[alfaminusculas])
    cta_madre = models.ForeignKey(
        'Cuenta',
        related_name='subcuentas',
        null=True, blank=True,
        on_delete=models.CASCADE,
    )
    opciones = models.CharField(max_length=8, default='i')
    _saldo = models.FloatField(default=0)

    class Meta:
        ordering = ('nombre', )

    @staticmethod
    def crear(nombre, slug, opciones='i', cta_madre=None):
        cuenta = Cuenta(
            nombre=nombre, slug=slug, opciones=opciones, cta_madre=cta_madre)
        cuenta.full_clean()
        cuenta.save()
        return cuenta

    def __str__(self):
        return self.nombre

    @property
    def tipo(self):
        if 'i' in self.opciones:
            return 'interactiva'
        if 'c' in self.opciones:
            return 'caja'
        raise ErrorOpciones('No se encontró switch de tipo')

    @tipo.setter
    def tipo(self, tipo):
        if tipo == 'caja':
            self.opciones = self.opciones.replace('i', 'c')
        elif tipo == 'interactiva':
            self.opciones = self.opciones.replace('c', 'i')
        else:
            raise ErrorOpciones(f'Opción no admitida: {tipo}')

    @property
    def saldo(self):
        return self._saldo

    @saldo.setter
    def saldo(self, saldo):
        self._saldo = saldo

    def full_clean(self, *args, **kwargs):
        self.slug = self.slug.lower()
        if 'c' not in self.opciones and 'i' not in self.opciones:
            raise ErrorOpciones('La cuenta no tiene tipo asignado')
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.esta_en_una_caja():
            try:
                saldo_guardado = Cuenta.tomar(slug=self.slug).saldo
            except Cuenta.DoesNotExist:
                saldo_guardado = 0.0
            if self.saldo != saldo_guardado:
                saldo_cm = self.cta_madre.saldo
                self.cta_madre.saldo += self.saldo
                self.cta_madre.saldo -= saldo_guardado
                self.cta_madre.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.saldo != 0:
            raise errors.SaldoNoCeroException
        super().delete(*args, **kwargs)

    def cantidad_movs(self):
        return self.entradas.count() + self.salidas.count()

    def total_movs(self):
        total_entradas = self.entradas.all() \
                             .aggregate(Sum('importe'))['importe__sum'] or 0
        total_salidas = self.salidas.all()\
                            .aggregate(Sum('importe'))['importe__sum'] or 0
        return total_entradas - total_salidas

    def corregir_saldo(self):
        self.saldo = self.total_movs()
        self.save()

    def saldo_ok(self):
        return self.saldo == self.total_movs()

    def agregar_mov_correctivo(self):
        if self.saldo_ok():
            return None
        saldo = self.saldo
        mov = Movimiento(concepto='Movimiento correctivo')
        mov.importe = self.saldo - self.total_movs()
        if mov.importe < 0:
            mov.importe = -mov.importe
            mov.cta_salida = self
        else:
            mov.cta_entrada = self
        try:
            mov.full_clean()
        except TypeError:
            raise TypeError(f'Error en mov {mov}')
        mov.save()
        self.saldo = saldo
        self.save()
        return mov

    def dividir_entre(self, subcuentas):
        for subcuenta in subcuentas:
            cta = Cuenta.crear(
                nombre=subcuenta['nombre'],
                slug=subcuenta['slug'],
                cta_madre=self,
            )
            Movimiento.crear(
                concepto=f'Paso de saldo de {self.nombre} '
                         f'a subcuenta {cta.nombre}',
                importe=subcuenta['saldo'],
                cta_entrada=cta,
                cta_salida=self,
            )
        self.tipo = 'caja'
        self.save()

    def esta_en_una_caja(self):
        return self.cta_madre is not None


class Movimiento(MiModel):
    fecha = MiDateField(default=hoy)
    concepto = models.CharField(max_length=80)
    detalle = models.TextField(blank=True, null=True)
    importe = models.FloatField()
    cta_entrada = models.ForeignKey(
        Cuenta, related_name='entradas', null=True, blank=True,
        on_delete=models.CASCADE
    )
    cta_salida = models.ForeignKey(
        Cuenta, related_name='salidas', null=True, blank=True,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('fecha', 'concepto', )

    def __str__(self):
        string = f'{self.fecha.strftime("%Y-%m-%d")} {self.concepto}: ' \
                 f'{self.importe}'
        if self.cta_entrada:
            string += f' +{self.cta_entrada}'
        if self.cta_salida:
            string += f' -{self.cta_salida}'
        return string

    def clean(self):
        super().clean()
        if not self.cta_entrada and not self.cta_salida:
            raise ValidationError(message=errors.CUENTA_INEXISTENTE)
        if self.cta_entrada == self.cta_salida:
            raise ValidationError(message=errors.CUENTAS_IGUALES)

    def delete(self, *args, **kwargs):
        if self.cta_entrada:
            self.cta_entrada.saldo -= self.importe
            self.cta_entrada.save()
        if self.cta_salida:
            self.cta_salida.saldo += self.importe
            self.cta_salida.save()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Movimiento nuevo
        if self._state.adding:
            if self.cta_entrada:
                self.cta_entrada.saldo += self.importe
                self.cta_entrada.save()
            if self.cta_salida:
                self.cta_salida.saldo -= self.importe
                self.cta_salida.save()

        # Movimiento existente
        else:
            mov_guardado = Movimiento.tomar(pk=self.pk)

            # No cambió la cuenta de entrada
            if self.cta_entrada == mov_guardado.cta_entrada:
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
                if self.cta_salida:
                    self.cta_salida.refresh_from_db()

            # No cambió la cuenta de salida
            if self.cta_salida == mov_guardado.cta_salida:
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
                    mov_guardado.cta_salida.saldo += mov_guardado.importe
                    mov_guardado.cta_salida.save()
                # Ahora hay una cuenta de salida
                if self.cta_salida:
                    self.cta_salida.saldo -= self.importe
                    self.cta_salida.save()

        super().save(*args, **kwargs)
