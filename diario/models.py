from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Sum

from utils import errors
from utils.clases.mimodel import MiModel
from utils.errors import \
    ErrorDeSuma, ErrorDependenciaCircular, ErrorOpciones, ErrorTipo


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
        if 'c' in self.opciones and 'i' in self.opciones:
            raise ErrorOpciones('La cuenta tiene más de un tipo asignado')
        if self.tipo == 'caja' and self.subcuentas.count() == 0:
            raise ErrorTipo('Cuenta caja debe tener subcuentas')
        if self.tipo == 'interactiva' and self.subcuentas.count() != 0:
            raise ErrorTipo('Cuenta interactiva no puede tener subcuentas')
        if self.cta_madre in self.arbol_de_subcuentas():
            raise ErrorDependenciaCircular(
                f'Cuenta madre {self.cta_madre} está entre las subcuentas '
                f'de {self} o entre las de una de sus subcuentas'
            )

        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.esta_en_una_caja():
            try:
                cta_guardada = Cuenta.tomar(slug=self.slug)
                saldo_guardado = cta_guardada.saldo
                cta_madre_guardada = cta_guardada.cta_madre
            except Cuenta.DoesNotExist:
                saldo_guardado = 0.0
                cta_madre_guardada = None
            if self.saldo != saldo_guardado:
                saldo_cm = self.cta_madre.saldo
                self.cta_madre.saldo += self.saldo
                self.cta_madre.saldo -= saldo_guardado
                self.cta_madre.save()
            if self.cta_madre and self.cta_madre != cta_madre_guardada:
                self.cta_madre.saldo += self.saldo
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
        subsaldos = [subc.get('saldo') for subc in subcuentas]

        if subsaldos.count(None) == 1:
            subcta_sin_saldo = subsaldos.index(None)
            subsaldos.pop(subcta_sin_saldo)
            subcuentas[subcta_sin_saldo]['saldo'] = self.saldo - sum(subsaldos)
            subsaldos.append(subcuentas[subcta_sin_saldo]['saldo'])

        if sum(subsaldos) != self.saldo:
            raise ErrorDeSuma(f'Suma errónea. Saldos de subcuentas '
                              f'deben sumar {self.saldo:.2f}')

        lista_subcuentas = list()
        for subcuenta in subcuentas:
            cta = Cuenta.crear(
                nombre=subcuenta['nombre'],
                slug=subcuenta['slug'],
                cta_madre=self,
            )
            Movimiento.crear(
                concepto=f'Paso de saldo de {self.nombre} '
                         f'a subcuenta {cta.nombre}'[:80],
                importe=subcuenta['saldo'],
                cta_entrada=cta,
                cta_salida=self,
            )
            lista_subcuentas.append(cta)
        self.tipo = 'caja'
        self.save()
        return lista_subcuentas

    def esta_en_una_caja(self):
        return self.cta_madre is not None

    def arbol_de_subcuentas(self):
        todas_las_subcuentas = set(self.subcuentas.all())
        for cuenta in self.subcuentas.all():
            todas_las_subcuentas.update(cuenta.arbol_de_subcuentas())
        return todas_las_subcuentas


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

    @property
    def sentido(self):
        if self.cta_entrada and self.cta_salida:
            return 't'
        if self.cta_entrada:
            return 'e'
        if self.cta_salida:
            return 's'

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
        if (self.cta_entrada and self.cta_entrada.tipo != 'interactiva') \
                or (self.cta_salida and self.cta_salida.tipo != 'interactiva'):
            raise ValidationError(message=errors.CUENTA_NO_INTERACTIVA)

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
