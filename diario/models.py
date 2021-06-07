from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse

from utils import errors
from utils.clases.mimodel import MiModel
from utils.errors import \
    ErrorDeSuma, ErrorDependenciaCircular, ErrorOpciones, ErrorTipo, \
    SaldoNoCeroException, SUBCUENTAS_SIN_SALDO


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

    @classmethod
    def crear(cls, nombre, slug, opciones='i', cta_madre=None, **kwargs):
        return super().crear(
            nombre=nombre,
            slug=slug,
            opciones=opciones,
            cta_madre=cta_madre,
            **kwargs
        )

    def __str__(self):
        return self.nombre

    @property
    def tipo(self):
        if 'i' in self.opciones:
            return 'interactiva'
        if 'c' in self.opciones:
            return 'caja'
        raise ErrorOpciones('No se encontró opción de tipo')

    @tipo.setter
    def tipo(self, tipo):
        if tipo == 'caja':
            self.opciones = self.opciones.replace('i', 'c')
        elif tipo == 'interactiva':
            self.opciones = self.opciones.replace('c', 'i')
        else:
            raise ErrorOpciones(f'Opción no admitida: {tipo}')

    @property
    def es_interactiva(self):
        return 'i' in self.opciones

    @property
    def es_caja(self):
        return 'c' in self.opciones

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
        if self.es_caja and self.subcuentas.count() == 0:
            raise ErrorTipo('Cuenta caja debe tener subcuentas')
        if self.es_interactiva and self.subcuentas.count() != 0:
            raise ErrorTipo('Cuenta interactiva no puede tener subcuentas')
        if self.cta_madre in self.arbol_de_subcuentas():
            raise ErrorDependenciaCircular(
                f'Cuenta madre {self.cta_madre} está entre las subcuentas '
                f'de {self} o entre las de una de sus subcuentas'
            )
        if self.cta_madre and self.cta_madre.es_interactiva:
            raise ErrorTipo(f'Cuenta interactiva "{self.cta_madre }" '
                            f'no puede ser madre')

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
            raise SaldoNoCeroException
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('cta_mod', args=[self.slug])

    def movs(self):
        result = self.entradas.all() | self.salidas.all()
        for sc in self.subcuentas.all():
            result = result | sc.movs()
        return result.order_by('fecha')

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

    def dividir_entre(self, *subcuentas):

        # Limpieza de los argumentos
        # Si se pasa una lista convertirla en argumentos sueltos
        if len(subcuentas) == 1 and type(subcuentas) in (list, tuple):
            subcuentas = subcuentas[0]

        cuentas_limpias = list()

        for i, subcuenta in enumerate(subcuentas):
            if type(subcuenta) in (list, tuple):
                try:
                    subcuenta = {
                        'nombre': subcuenta[0],
                        'slug': subcuenta[1],
                        'saldo': subcuenta[2]
                    }
                except IndexError:
                    subcuenta = {'nombre': subcuenta[0], 'slug': subcuenta[1]}

            try:
                saldo = subcuenta['saldo']
            except KeyError:
                subcuenta['saldo'] = 0
                try:
                    subcuenta['saldo'] = \
                        self.saldo - sum([x['saldo'] for x in subcuentas])
                except TypeError:
                    subcus = list(subcuentas)[:i] + list(subcuentas)[i+1:]
                    try:
                        subcuenta['saldo'] = \
                            self.saldo - sum([x[2] for x in subcus])
                    except IndexError:
                        raise ErrorDeSuma(SUBCUENTAS_SIN_SALDO)
                except KeyError:
                    raise ErrorDeSuma(SUBCUENTAS_SIN_SALDO)
            cuentas_limpias.append(subcuenta)

        if sum([x['saldo'] for x in cuentas_limpias]) != self.saldo:
            raise ErrorDeSuma(f'Suma errónea. Saldos de subcuentas '
                              f'deben sumar {self.saldo:.2f}')

        # Generación de subcuentas y traspaso de saldos
        self.tipo = 'caja'
        cuentas_creadas = list()
        for i, subcuenta in enumerate(cuentas_limpias):
            saldo = subcuenta.pop('saldo')
            cuentas_creadas.append(Cuenta.crear(**subcuenta, cta_madre=self))
            self.tipo = 'interactiva'
            Movimiento.crear(
                concepto=f'Paso de saldo de {self.nombre} '
                         f'a subcuenta {cuentas_creadas[i].nombre}'[:80],
                importe=saldo,
                cta_entrada=cuentas_creadas[i],
                cta_salida=self,
            )
            self.tipo = 'caja'
        self.save()
        return cuentas_creadas

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
        ordering = ('fecha', )

    @property
    def sentido(self):
        if self.cta_entrada and self.cta_salida:
            return 't'
        if self.cta_entrada:
            return 'e'
        return 's'

    def __str__(self):
        string = f'{self.fecha.strftime("%Y-%m-%d")} {self.concepto}: ' \
                 f'{self.importe}'
        if self.cta_entrada:
            string += f' +{self.cta_entrada}'
        if self.cta_salida:
            string += f' -{self.cta_salida}'
        return string

    @classmethod
    def crear(cls, concepto, importe, cta_entrada=None, cta_salida=None,
              **kwargs):
        return super().crear(
            concepto=concepto,
            importe=importe,
            cta_entrada=cta_entrada,
            cta_salida=cta_salida,
            **kwargs
        )

    def clean(self):
        super().clean()
        if not self.cta_entrada and not self.cta_salida:
            raise ValidationError(message=errors.CUENTA_INEXISTENTE)
        if self.cta_entrada == self.cta_salida:
            raise ValidationError(message=errors.CUENTAS_IGUALES)
        if (self.cta_entrada and not self.cta_entrada.es_interactiva) \
                or (self.cta_salida and not self.cta_salida.es_interactiva):
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
