from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse

from diario.managers import PolymorphManager
from utils import errors
from utils.clases.mimodel import MiModel
from utils.errors import \
    ErrorCuentaEsInteractiva, ErrorDeSuma, ErrorDependenciaCircular, \
    ErrorOpciones, ErrorTipo, SaldoNoCeroException, SUBCUENTAS_SIN_SALDO


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
        'CuentaAcumulativa',
        related_name='subcuentas',
        null=True, blank=True,
        on_delete=models.CASCADE,
    )
    opciones = models.CharField(max_length=8, default='i')
    _saldo = models.FloatField(default=0)
    content_type = models.ForeignKey(
        ContentType,
        null=True, editable=False, on_delete=models.CASCADE,
    )

    objects = PolymorphManager()

    class Meta:
        ordering = ('nombre', )

    @classmethod
    def crear(cls, nombre, slug, opciones='i', cta_madre=None, finalizar=False,
              **kwargs):

        try:
            saldo = kwargs.pop('saldo')
        except KeyError:
            saldo = None

        if finalizar:
            cuenta_nueva = super().crear(
                nombre=nombre,
                slug=slug,
                opciones=opciones,
                cta_madre=cta_madre,
                **kwargs
            )
        else:
            cuenta_nueva = CuentaInteractiva.crear(
                nombre=nombre,
                slug=slug,
                opciones=opciones,
                cta_madre=cta_madre,
                **kwargs
            )

        if saldo:
            Movimiento.crear(
                concepto=f'Saldo inicial de {cuenta_nueva.nombre}',
                importe=saldo,
                cta_entrada=cuenta_nueva
            )

        return cuenta_nueva

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
        return isinstance(self, CuentaInteractiva)

    @property
    def es_acumulativa(self):
        return isinstance(self, CuentaAcumulativa)

    @property
    def saldo(self):
        return self._saldo

    @saldo.setter
    def saldo(self, saldo):
        self._saldo = saldo

    def full_clean(self, *args, **kwargs):
        if self.slug:
            self.slug = self.slug.lower()
        if self.nombre:
            self.nombre = self.nombre.lower()

        if 'c' not in self.opciones and 'i' not in self.opciones:
            raise ErrorOpciones('La cuenta no tiene tipo asignado')
        if 'c' in self.opciones and 'i' in self.opciones:
            raise ErrorOpciones('La cuenta tiene más de un tipo asignado')
        if self.es_acumulativa and self.subcuentas.count() == 0:
            raise ErrorTipo('Cuenta caja debe tener subcuentas')
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
                self.cta_madre.saldo += self.saldo
                self.cta_madre.saldo -= saldo_guardado
                self.cta_madre.save()
            if self.cta_madre and self.cta_madre != cta_madre_guardada:
                self.cta_madre.saldo += self.saldo

        if not self.content_type:
            self.content_type = ContentType.objects.get(
                app_label=self._meta.app_label,
                model=self.get_lower_class_name()
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.saldo != 0:
            raise SaldoNoCeroException
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('cta_detalle', args=[self.slug])

    @classmethod
    def get_lower_class_name(cls):
        return cls.__name__.lower()

    def como_subclase(self, database='default'):
        content_type = self.content_type
        model = content_type.model_class()
        if model == Cuenta:
            return self
        return model.tomar(pk=self.pk, polymorphic=False, using=database)

    def movs_directos(self):
        """ Devuelve entradas y salidas de la cuenta"""
        return self.entradas.all() | self.salidas.all()

    def movs(self):
        """ Devuelve movimientos propios y de sus subcuentas
            ordenados por fecha."""
        return self.movs_directos().order_by('fecha')

    def cantidad_movs(self):
        return self.entradas.count() + self.salidas.count()

    def total_subcuentas(self):
        if self.es_interactiva:
            raise ErrorCuentaEsInteractiva(
                f'Cuenta "{self.nombre}" es interactiva y como tal no tiene '
                f'subcuentas'
            )
        return self.subcuentas.all().aggregate(Sum('_saldo'))['_saldo__sum']

    def total_movs(self):
        """ Devuelve suma de los importes de los movimientos de la cuenta"""
        total_entradas = self.entradas.all() \
                             .aggregate(Sum('importe'))['importe__sum'] or 0
        total_salidas = self.salidas.all()\
                            .aggregate(Sum('importe'))['importe__sum'] or 0
        return total_entradas - total_salidas

    def corregir_saldo(self):
        if self.es_interactiva:
            self.saldo = self.total_movs()
        else:
            self.saldo = self.total_subcuentas()
        self.save()

    def saldo_ok(self):
        if self.es_interactiva:
            return self.saldo == self.total_movs()
        else:
            return self.saldo == self.total_subcuentas()

    def dividir_entre(self, *subcuentas):

        # Limpieza de los argumentos
        # Si se pasa una lista convertirla en argumentos sueltos
        if len(subcuentas) == 1 and type(subcuentas) in (list, tuple):
            subcuentas = subcuentas[0]

        cuentas_limpias = list()

        # Verificar que todas las subcuentas tengan saldo y tomar las
        # acciones correspondientes en caso de que no
        for i, subcuenta in enumerate(subcuentas):
            if type(subcuenta) in (list, tuple):
                try:
                    subcuenta = {
                        'nombre': subcuenta[0],
                        'slug': subcuenta[1],
                        'saldo': subcuenta[2]
                    }
                except IndexError:  # No hay elemento para saldo
                    subcuenta = {'nombre': subcuenta[0], 'slug': subcuenta[1]}

            try:
                subcuenta['saldo'] = float(subcuenta['saldo'])
            except KeyError:    # El dict no tiene clave 'saldo'
                subcuenta['saldo'] = 0.0
                try:
                    subcuenta['saldo'] = self.saldo - sum([
                        x['saldo'] for x in subcuentas
                    ])
                except TypeError:
                    subcus = list(subcuentas)[:i] + list(subcuentas)[i+1:]
                    try:
                        subcuenta['saldo'] = \
                            self.saldo - sum([x[2] for x in subcus])
                    except IndexError:  # Hay más de una subcuenta sin saldo
                        raise ErrorDeSuma(SUBCUENTAS_SIN_SALDO)
                except KeyError:    # Hay más de una subcuenta sin saldo
                    raise ErrorDeSuma(SUBCUENTAS_SIN_SALDO)
            cuentas_limpias.append(subcuenta)

        if sum([x['saldo'] for x in cuentas_limpias]) != self.saldo:
            raise ErrorDeSuma(f'Suma errónea. Saldos de subcuentas '
                              f'deben sumar {self.saldo:.2f}')

        # Un movimiento de salida por cada una de las subcuentas
        # (después de generar cada subcuenta se generará el movimiento de
        # entrada correspondiente).
        for subcuenta in cuentas_limpias:
            try:
                Movimiento.crear(
                    concepto=f'Saldo pasado por {self.nombre.capitalize()} '
                             f'a nueva subcuenta {subcuenta["nombre"]}',
                    importe=subcuenta['saldo'],
                    cta_salida=self,
                )
            except errors.ErrorImporteCero:
                # Si el saldo de la subcuenta es 0, no generar movimiento
                pass

        # Generación de subcuentas y traspaso de saldos
        cta_madre = self.convertirse_en_acumulativa()

        cuentas_creadas = list()

        for i, subcuenta in enumerate(cuentas_limpias):
            saldo = subcuenta.pop('saldo')
            cuentas_creadas.append(Cuenta.crear(**subcuenta, cta_madre=cta_madre))

            # Se generan movimientos de entrada correspondientes a los
            # movimientos de salida en cta_madre
            try:
                Movimiento.crear(
                    concepto=f'Saldo recibido '
                             f'por {cuentas_creadas[i].nombre.capitalize()} de'
                             f' cuenta madre {self.nombre.capitalize()}'[:80],
                    importe=saldo,
                    cta_entrada=cuentas_creadas[i],
                )
            except errors.ErrorImporteCero:
                # Si el saldo de la subcuenta es 0, no generar movimiento
                pass

        return cuentas_creadas

    def dividir_y_actualizar(self, *subcuentas):
        self.dividir_entre(*subcuentas)
        return Cuenta.tomar(slug=self.slug)

    def esta_en_una_caja(self):
        return self.cta_madre is not None


class CuentaInteractiva(Cuenta):

    @classmethod
    def crear(cls, nombre, slug, opciones='i', cta_madre=None, **kwargs):
        return super().crear(
            nombre=nombre,
            slug=slug,
            opciones=opciones,
            cta_madre=cta_madre,
            finalizar=True,
            **kwargs)

    def convertirse_en_acumulativa(self):
        pk_preservado = self.pk
        self.delete(keep_parents=True)
        cuenta = Cuenta.objects.get_no_poly(pk=pk_preservado)
        cuenta_acumulativa = CuentaAcumulativa(cuenta_ptr_id=cuenta.pk)
        cuenta_acumulativa.__dict__.update(cuenta.__dict__)
        cuenta_acumulativa.content_type = ContentType.objects.get(
            app_label='diario', model='cuentaacumulativa'
        )
        cuenta_acumulativa.fecha_conversion = date.today()
        cuenta_acumulativa.save()
        return cuenta_acumulativa

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


class CuentaAcumulativa(Cuenta):

    fecha_conversion = models.DateField()

    def arbol_de_subcuentas(self):
        todas_las_subcuentas = set(self.subcuentas.all())
        for cuenta in self.subcuentas.all():
            if isinstance(cuenta, CuentaAcumulativa):
                todas_las_subcuentas.update(cuenta.arbol_de_subcuentas())
        return todas_las_subcuentas

    def full_clean(self, *args, **kwargs):
        if self.cta_madre in self.arbol_de_subcuentas():
            raise ErrorDependenciaCircular(
                f'Cuenta madre {self.cta_madre.nombre.capitalize()} está '
                f'entre las subcuentas de {self.nombre.capitalize()} o entre '
                f'las de una de sus subcuentas'
            )
        super().full_clean(*args, **kwargs)

    def movs(self):
        """ Devuelve movimientos propios y de sus subcuentas
            ordenados por fecha."""
        result = super().movs()
        for sc in self.subcuentas.all():
            result = result | sc.movs()
        return result.order_by('fecha')


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
        importe = float(importe)

        if importe == 0:
            raise errors.ErrorImporteCero(
                'Se intentó crear un movimiento con importe cero')
        if importe < 0:
            importe = -importe
            cuenta = cta_salida
            cta_salida = cta_entrada
            cta_entrada = cuenta

        return super().crear(
            concepto=concepto,
            importe=importe,
            cta_entrada=cta_entrada,
            cta_salida=cta_salida,
            **kwargs
        )

    @classmethod
    def tomar(cls, polymorphic=True, *args, **kwargs):
        mov = super().tomar(polymorphic, *args, **kwargs)
        if mov.cta_entrada:
            mov.cta_entrada = Cuenta.tomar(pk=mov.cta_entrada.pk)
        if mov.cta_salida:
            mov.cta_salida = Cuenta.tomar(pk=mov.cta_salida.pk)
        return mov

    def clean(self):
        super().clean()
        if not self.cta_entrada and not self.cta_salida:
            raise ValidationError(message=errors.CUENTA_INEXISTENTE)
        if self.cta_entrada == self.cta_salida:
            raise ValidationError(message=errors.CUENTAS_IGUALES)
        # TODO: mejorar redacción de esto
        if (hasattr(self.cta_entrada, 'fecha_conversion')
                and self.fecha > self.cta_entrada.fecha_conversion) \
            or (hasattr(self.cta_salida, 'fecha_conversion')
                and self.fecha > self.cta_salida.fecha_conversion):
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
            try:
                entradas_iguales = (
                        self.cta_entrada.pk == mov_guardado.cta_entrada.pk)
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
                if self.cta_salida:
                    self.cta_salida.refresh_from_db()

            # No cambió la cuenta de salida
            try:
                salidas_iguales = (
                        self.cta_salida.pk == mov_guardado.cta_salida.pk)
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
