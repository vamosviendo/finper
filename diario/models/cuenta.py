from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse

from diario.models.titular import Titular
from diario.models.movimiento import Movimiento
from utils import errors
from utils.iterables import remove_duplicates
from vvmodel.models import PolymorphModel


alfaminusculas = RegexValidator(
    r'^[0-9a-z]*$', 'Solamente caracteres alfanuméricos')


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
    titular = models.ForeignKey('diario.Titular',
                                related_name='cuentas',
                                on_delete=models.CASCADE,
                                null=True, blank=True,
                                default=Titular.por_defecto)

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
        return str(self.content_type) == 'diario | cuenta interactiva'

    @property
    def es_acumulativa(self):
        return str(self.content_type) == 'diario | cuenta acumulativa'

    @property
    def saldo(self):
        return self._saldo

    @saldo.setter
    def saldo(self, valor):
        self._saldo = round(valor, 2)

    def full_clean(self, *args, **kwargs):
        if self.slug:
            self.slug = self.slug.lower()
        if self.nombre:
            self.nombre = self.nombre.lower()
        if self.es_acumulativa and self.como_subclase().subcuentas.count()== 0:
            raise errors.ErrorTipo('Cuenta caja debe tener subcuentas')
        if self.cta_madre and self.cta_madre.es_interactiva:
            raise errors.ErrorTipo(f'Cuenta interactiva "{self.cta_madre }" '
                                   f'no puede ser madre')

        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.tiene_madre():
            self._actualizar_madre()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.saldo != 0:
            raise errors.SaldoNoCeroException
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('cta_detalle', args=[self.slug])

    def movs_directos(self):
        """ Devuelve entradas y salidas de la cuenta sin los de sus subcuentas
        """
        return self.entradas.all() | self.salidas.all()

    def movs(self):
        """ Devuelve movimientos propios y de sus subcuentas
            ordenados por fecha.
            Antes de protestar que devuelve lo mismo que movs_directos()
            tener en cuenta que está sobrescrita en CuentaAcumulativa
            """
        return self.movs_directos().order_by('fecha')

    def cantidad_movs(self):
        return self.entradas.count() + self.salidas.count()

    def total_movs(self):
        """ Devuelve suma de los importes de los movimientos de la cuenta"""
        total_entradas = self.entradas.all() \
                             .aggregate(Sum('_importe'))['_importe__sum'] or 0
        total_salidas = self.salidas.all()\
                            .aggregate(Sum('_importe'))['_importe__sum'] or 0

        return round(total_entradas - total_salidas, 2)

    def fecha_ultimo_mov_directo(self):
        try:
            return self.movs_directos().order_by('fecha').last().fecha
        except AttributeError:
            return None

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

    def dividir_entre(self, *subcuentas, fecha=None):
        fecha = fecha or date.today()
        try:
            if fecha < self.fecha_ultimo_mov_directo():
                raise errors.ErrorMovimientoPosteriorAConversion
        except TypeError:
            pass

        if not self.saldo_ok():
            raise ValidationError(
                f'Saldo de cuenta "{self.nombre}" no coincide '
                f'con sus movimientos. Verificar'
            )

        cuentas_limpias = self._ajustar_subcuentas(subcuentas)

        movimientos_incompletos = self._vaciar_saldo(cuentas_limpias, fecha)

        cta_madre = self._convertirse_en_acumulativa(fecha)

        cuentas_creadas = self._generar_subcuentas(
            cuentas_limpias, movimientos_incompletos, cta_madre
        )
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

            dic_subcuenta = self._asegurar_dict(subcuenta)

            if 'titular' not in dic_subcuenta.keys():
                dic_subcuenta.update({'titular': self.titular})

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

    @staticmethod
    def _asegurar_dict(subcuenta):
        """ Recibe un dict, lista o tupla con información de cuenta y
            los convierte a dict si es necesario."""
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

        return dic_subcuenta

    def _convertirse_en_acumulativa(self, fecha=None):
        fecha = fecha or date.today()
        pk_preservado = self.pk

        self.delete(keep_parents=True)
        cuenta = Cuenta.objects.get_no_poly(pk=pk_preservado)
        cuenta_acumulativa = CuentaAcumulativa(cuenta_ptr_id=cuenta.pk)
        cuenta_acumulativa.__dict__.update(cuenta.__dict__)
        cuenta_acumulativa.content_type = ContentType.objects.get(
            app_label='diario', model='cuentaacumulativa'
        )
        cuenta_acumulativa.fecha_conversion = fecha
        cuenta_acumulativa.save()
        return cuenta_acumulativa

    def _vaciar_saldo(self, cuentas_limpias, fecha=None):
        fecha = fecha or date.today()
        movimientos_incompletos = []

        for subcuenta in cuentas_limpias:

            try:
                movimientos_incompletos.append(Movimiento.crear(
                    fecha=fecha,
                    concepto="Traspaso de saldo",
                    detalle=f'Saldo pasado por {self.nombre.capitalize()} ' 
                            f'a nueva subcuenta '
                            f'{subcuenta["nombre"].lower().capitalize()}',
                    importe=subcuenta.pop('saldo'),
                    cta_salida=self,
                ))
            except errors.ErrorImporteCero:
                # Si el saldo de la subcuenta es 0, no generar movimiento
                movimientos_incompletos.append(None)

        return movimientos_incompletos

    @staticmethod
    def _generar_subcuentas(
            cuentas_limpias, movimientos_incompletos, cta_madre):

        cuentas_creadas = list()

        for i, subcuenta in enumerate(cuentas_limpias):
            cuentas_creadas.append(
                Cuenta.crear(**subcuenta, cta_madre=cta_madre)
            )

            if movimientos_incompletos[i] is not None:
                movimientos_incompletos[i].cta_entrada = cuentas_creadas[i]
                movimientos_incompletos[i].save()

        return cuentas_creadas


class CuentaAcumulativa(Cuenta):

    fecha_conversion = models.DateField()

    @property
    def titulares(self):
        titulares = list()
        subcuentas = list(self.subcuentas.all())

        for subcuenta in subcuentas:
            if subcuenta.es_interactiva:
                titulares.append(subcuenta.titular)
            else:
                titulares += subcuenta.titulares

        return remove_duplicates(titulares)

    def arbol_de_subcuentas(self):
        todas_las_subcuentas = set(self.subcuentas.all())
        for cuenta in self.subcuentas.all():
            if cuenta.es_acumulativa:
                todas_las_subcuentas.update(cuenta.arbol_de_subcuentas())
        return todas_las_subcuentas

    def corregir_saldo(self):
        self.saldo = self.total_subcuentas()
        self.save()

    def saldo_ok(self):
        return self.saldo == self.total_subcuentas()

    def full_clean(self, *args, **kwargs):
        if self.cta_madre in self.arbol_de_subcuentas():
            raise errors.ErrorDependenciaCircular(
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

    def agregar_subcuenta(self, lista_subcuenta):
        Cuenta.crear(*lista_subcuenta, cta_madre=self)
