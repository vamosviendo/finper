from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse

from utils import errors
from utils.errors import ErrorDeSuma, ErrorDependenciaCircular, \
    ErrorOpciones, ErrorTipo, SaldoNoCeroException, SUBCUENTAS_SIN_SALDO
from vvmodel.models import MiModel, PolymorphModel


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


class Cuenta(PolymorphModel):
    nombre = models.CharField(max_length=50, unique=True)
    slug = models.CharField(
        max_length=4, unique=True, validators=[alfaminusculas])
    cta_madre = models.ForeignKey(
        'CuentaAcumulativa',
        related_name='subcuentas',
        null=True, blank=True,
        on_delete=models.CASCADE,
    )
    _saldo = models.FloatField(default=0)

    class Meta:
        ordering = ('nombre', )

    @classmethod
    def crear(cls, nombre, slug, cta_madre=None, finalizar=False, **kwargs):

        if finalizar:
            cuenta_nueva = super().crear(nombre=nombre, slug=slug,
                                         cta_madre=cta_madre, **kwargs)
        else:
            cuenta_nueva = CuentaInteractiva.crear(nombre=nombre, slug=slug,
                                                   cta_madre=cta_madre,
                                                   **kwargs)

        return cuenta_nueva

    def __str__(self):
        return self.nombre

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
        if self.es_acumulativa and self.subcuentas.count() == 0:
            raise ErrorTipo('Cuenta caja debe tener subcuentas')
        if self.cta_madre and self.cta_madre.es_interactiva:
            raise ErrorTipo(f'Cuenta interactiva "{self.cta_madre }" '
                            f'no puede ser madre')

        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.tiene_madre():
            self._actualizar_madre()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.saldo != 0:
            raise SaldoNoCeroException
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('cta_detalle', args=[self.slug])

    def movs_directos(self):
        """ Devuelve entradas y salidas de la cuenta sin los de sus subcuentas
        """
        return self.entradas.all() | self.salidas.all()

    def movs(self):
        """ Devuelve movimientos propios y de sus subcuentas
            ordenados por fecha."""
        return self.movs_directos().order_by('fecha')

    def cantidad_movs(self):
        return self.entradas.count() + self.salidas.count()

    def total_movs(self):
        """ Devuelve suma de los importes de los movimientos de la cuenta"""
        total_entradas = self.entradas.all() \
                             .aggregate(Sum('importe'))['importe__sum'] or 0
        total_salidas = self.salidas.all()\
                            .aggregate(Sum('importe'))['importe__sum'] or 0
        return total_entradas - total_salidas

    def tiene_madre(self):
        return self.cta_madre is not None

    # Métodos protegidos

    def _actualizar_madre(self):
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


class CuentaInteractiva(Cuenta):

    @classmethod
    def crear(cls, nombre, slug, cta_madre=None, saldo=None, **kwargs):

        cuenta_nueva = super().crear(nombre=nombre, slug=slug,
                                     cta_madre=cta_madre, finalizar=True,
                                     **kwargs)

        if saldo:
            Movimiento.crear(
                concepto=f'Saldo inicial de {cuenta_nueva.nombre}',
                importe=saldo,
                cta_entrada=cuenta_nueva
            )

        return cuenta_nueva

    def corregir_saldo(self):
        self.saldo = self.total_movs()
        self.save()

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

    def saldo_ok(self):
        return self.saldo == self.total_movs()

    def dividir_entre(self, *subcuentas):

        cuentas_limpias = self._ajustar_subcuentas(subcuentas)

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
        cta_madre = self._convertirse_en_acumulativa()

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

    # Protected

    def _ajustar_subcuentas(self, subcuentas):
        """ Verificar que todas las subcuentas sean diccionarios y
            que todas tengan saldo y tomar las acciones correspondientes
            en caso de que no sea así."""
        if len(subcuentas) == 1 and type(subcuentas) in (list, tuple):
            subcuentas = subcuentas[0]

        subcuentas_limpias = list()

        for i, subcuenta in enumerate(subcuentas):

            # TODO Cuenta._asegurar_dict_subcuenta()
            # Asegurarse de que subcuenta venga en un dict
            if type(subcuenta) in (tuple, list):
                dic_subcuenta = {
                    'nombre': subcuenta[0],
                    'slug': subcuenta[1],
                }
                try:
                    dic_subcuenta['saldo'] = subcuenta[2]
                except IndexError:  # subcuenta no tiene saldo
                    dic_subcuenta['saldo'] = None
            else:
                dic_subcuenta = subcuenta

            # Completar subcuenta sin saldo
            if dic_subcuenta.get('saldo', None) is None:
                otras_subcuentas = subcuentas[:i] + subcuentas[i+1:]
                try:
                    total_otras_subcuentas = sum(
                        [float(x['saldo']) for x in otras_subcuentas]
                    )
                except TypeError:  # No es un dict. Suponemos iterable.
                    try:
                        total_otras_subcuentas = sum(
                            [float(x[2]) for x in otras_subcuentas]
                        )
                    except IndexError:  # Más de una subcuenta sin saldo
                        raise errors.ErrorDeSuma(
                            "Sólo se permite una subcuenta sin saldo."
                        )
                except KeyError:  # Más de una subcuenta sin saldo
                    raise errors.ErrorDeSuma

                dic_subcuenta['saldo'] = self.saldo - total_otras_subcuentas

            # Si saldo no es float, convertir
            dic_subcuenta['saldo'] = float(dic_subcuenta['saldo'])
            subcuentas_limpias.append(dic_subcuenta)

        # En este punto suma saldos subcuentas debe ser igual a self.saldo
        if sum([x['saldo'] for x in subcuentas_limpias]) != self.saldo:
            raise errors.ErrorDeSuma(
                f"Suma errónea. Saldos de subcuentas "
                f"deben sumar {self.saldo:.2f}"
            )

        return subcuentas_limpias

    def _convertirse_en_acumulativa(self):
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


class CuentaAcumulativa(Cuenta):

    fecha_conversion = models.DateField()

    def arbol_de_subcuentas(self):
        todas_las_subcuentas = set(self.subcuentas.all())
        for cuenta in self.subcuentas.all():
            if isinstance(cuenta, CuentaAcumulativa):
                todas_las_subcuentas.update(cuenta.arbol_de_subcuentas())
        return todas_las_subcuentas

    def corregir_saldo(self):
        self.saldo = self.total_subcuentas()
        self.save()

    def saldo_ok(self):
        return self.saldo == self.total_subcuentas()

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

    def total_subcuentas(self):
        return self.subcuentas.all().aggregate(Sum('_saldo'))['_saldo__sum']


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
