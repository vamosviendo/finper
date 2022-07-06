from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse

from utils.tiempo import Posicion
from diario.models.titular import Titular
from diario.models.movimiento import Movimiento
from diario.models.saldo import Saldo
from utils import errors
from utils.iterables import remove_duplicates
from vvmodel.models import PolymorphModel


alfaminusculas = RegexValidator(
    r'^[0-9a-z_\-]*$', 'Solamente caracteres alfanuméricos y guiones')


def signo(condicion):
    return 1 if condicion else -1


class Cuenta(PolymorphModel):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.CharField(
        max_length=20, unique=True, validators=[alfaminusculas])
    cta_madre = models.ForeignKey(
        'CuentaAcumulativa',
        related_name='subcuentas',
        null=True, blank=True,
        on_delete=models.CASCADE,
    )
    titular = models.ForeignKey('diario.Titular',
                                related_name='cuentas',
                                on_delete=models.CASCADE,
                                blank=True,
                                default=Titular.por_defecto)
    fecha_creacion = models.DateField(default=date.today)

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
    def es_cuenta_credito(self):
        return self.has_not_none_attr('contracuenta')

    @property
    def saldo(self):
        try:
            return self.ultimo_saldo.importe
        except AttributeError:
            return 0

    def saldo_historico(self, movimiento):
        try:
            return Saldo.tomar(cuenta=self, movimiento=movimiento).importe

        except Saldo.DoesNotExist:
            return 0

    def saldo_en_mov(self, movimiento):
        return Saldo.tomar(cuenta=self, movimiento=movimiento).importe

    def recalcular_saldos_entre(self,
                                pos_desde=Posicion(orden_dia=0),
                                pos_hasta=Posicion(orden_dia=100000000)):
        pos_hasta.fecha = pos_hasta.fecha or date.today()
        pos_hasta.orden_dia = pos_hasta.orden_dia or 100000000

        saldos = Saldo.posteriores_a(self, pos_desde, inclusive_od=True) & \
                 Saldo.anteriores_a(self, pos_hasta, inclusive_od=True)
        for saldo in saldos:
            try:
                saldo.importe = saldo.anterior().importe + (
                    signo(saldo.viene_de_entrada)*saldo.movimiento.importe
                )
            except AttributeError:
                saldo.importe = \
                    signo(saldo.viene_de_entrada)*saldo.movimiento.importe
            saldo.save()

    @property
    def ultimo_saldo(self):
        return self.saldo_set.last()

    def clean_fields(self, exclude=None):
        self._pasar_nombre_y_slug_a_minuscula()
        super().clean_fields(exclude=exclude)

    def clean(self, *args, **kwargs):
        self._impedir_cambio_de_titular()
        self._impedir_cambio_de_cta_madre()
        self._chequear_incongruencias_de_clase()

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

    def movs_directos_en_fecha(self, fecha):
        """ Devuelve movimientos directos de la cuenta en una fecha dada"""
        return self.movs_directos().filter(fecha=fecha)

    def movs(self, order_by='fecha'):
        """ Devuelve movimientos propios y de sus subcuentas
            ordenados por fecha.
            Antes de protestar que devuelve lo mismo que movs_directos()
            tener en cuenta que está sobrescrita en CuentaAcumulativa
            """
        return self.movs_directos().order_by(order_by)

    def movs_en_fecha(self, fecha):
        """ Devuelve movimientos propios y de sus subcuentas en una fecha dada.
        Ver comentario anterior."""
        return self.movs().filter(fecha=fecha)

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

    def tomar_de_bd(self):
        return Cuenta.tomar_o_nada(slug=self.slug)

    def hermanas(self):
        if self.cta_madre:
            return self.cta_madre.subcuentas.all().exclude(pk=self.pk)
        return None

    def ancestros(self):
        cta_madre = self.cta_madre
        lista_ancestros = []

        while cta_madre:
            lista_ancestros.append(cta_madre)
            cta_madre = cta_madre.cta_madre

        return lista_ancestros

    # Métodos protegidos

    def _actualizar_madre(self):

        try:
            saldo_guardado = Cuenta.tomar(slug=self.slug).saldo
        except Cuenta.DoesNotExist:
            saldo_guardado = 0.0

        if self.saldo != saldo_guardado:
            self.cta_madre.saldo += self.saldo
            self.cta_madre.saldo -= saldo_guardado
            self.cta_madre.save()

    def _pasar_nombre_y_slug_a_minuscula(self):
        if self.slug:
            self.slug = self.slug.lower()
        if self.nombre:
            self.nombre = self.nombre.lower()

    def _chequear_incongruencias_de_clase(self):
        if self.es_acumulativa and self.como_subclase().subcuentas.count()== 0:
            raise errors.ErrorTipo('Cuenta acumulativa debe tener subcuentas')
        if self.cta_madre and self.cta_madre.es_interactiva:
            raise errors.ErrorTipo(f'Cuenta interactiva "{self.cta_madre }" '
                                   f'no puede ser madre')

    def _impedir_cambio_de_cta_madre(self):
        try:
            cta_madre_guardada = Cuenta.tomar(slug=self.slug).cta_madre
            if self.cta_madre != cta_madre_guardada:
                raise ValidationError('No se puede modificar cuenta madre')
        except Cuenta.DoesNotExist:
            pass

    def _impedir_cambio_de_titular(self):
        try:
            titular_guardado = Cuenta.tomar(slug=self.slug).titular
            if self.titular != titular_guardado:
                raise errors.CambioDeTitularException
        except Cuenta.DoesNotExist:
            pass


class CuentaInteractiva(Cuenta):

    _contracuenta = models.OneToOneField(
        'diario.CuentaInteractiva',
        null=True, blank=True,
        related_name='_cuentacontra',
        on_delete=models.CASCADE
    )

    @classmethod
    def crear(cls, nombre, slug, cta_madre=None, saldo=None, **kwargs):

        cuenta_nueva = super().crear(nombre=nombre, slug=slug,
                                     cta_madre=cta_madre, finalizar=True,
                                     **kwargs)

        if saldo and float(saldo) != 0.0:
            Movimiento.crear(
                concepto=f'Saldo inicial de {cuenta_nueva.nombre}',
                importe=saldo,
                cta_entrada=cuenta_nueva,
                fecha=cuenta_nueva.fecha_creacion
            )

        return cuenta_nueva

    @property
    def contracuenta(self):
        if self._contracuenta:
            return self._contracuenta

        try:
            return self._cuentacontra
        except CuentaInteractiva._cuentacontra.RelatedObjectDoesNotExist:
            return None

    @contracuenta.setter
    def contracuenta(self, cuenta):
        self._contracuenta = cuenta

    def cargar_saldo(self, importe, fecha=None):
        fecha = fecha or date.today()

        if importe > 0:
            Movimiento.crear(
                concepto='Carga de saldo',
                importe=importe,
                cta_entrada=self,
                fecha=fecha
            )
        elif importe < 0:
            Movimiento.crear(
                concepto='Carga de saldo',
                importe=-importe,
                cta_salida=self,
                fecha=fecha
            )

    def corregir_saldo(self):
        saldo = self.ultimo_saldo
        saldo.importe = self.total_movs()
        saldo.save()

    def agregar_mov_correctivo(self):
        if self.saldo_ok():
            return None
        saldo = self.ultimo_saldo
        importe = saldo.importe
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
        saldo = self.ultimo_saldo
        saldo.importe = importe
        saldo.save()
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
            cuentas_limpias, movimientos_incompletos, cta_madre, fecha
        )
        return cuentas_creadas

    def dividir_y_actualizar(self, *subcuentas, fecha=None):
        self.dividir_entre(*subcuentas, fecha=fecha)
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

            if ('titular' not in dic_subcuenta.keys()
                or dic_subcuenta['titular'] is None):
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
        cuenta_acumulativa._state.adding = True
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
                    esgratis=subcuenta.pop('esgratis', False),
                ))
            except errors.ErrorImporteCero:
                # Si el saldo de la subcuenta es 0, no generar movimiento
                movimientos_incompletos.append(None)

        return movimientos_incompletos

    @staticmethod
    def _generar_subcuentas(
            cuentas_limpias, movimientos_incompletos, cta_madre, fecha):

        cuentas_creadas = list()

        for i, subcuenta in enumerate(cuentas_limpias):
            cuentas_creadas.append(
                Cuenta.crear(
                    **subcuenta,
                    cta_madre=cta_madre,
                    fecha_creacion=fecha
                )
            )

            if movimientos_incompletos[i] is not None:
                if movimientos_incompletos[i].cta_salida is not None:
                    movimientos_incompletos[i].cta_entrada = cuentas_creadas[i]
                elif movimientos_incompletos[i].cta_entrada is not None:
                    movimientos_incompletos[i].cta_salida = cuentas_creadas[i]
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

    @property
    def saldo(self):
        return sum([subc.saldo for subc in self.subcuentas.all()])

    def clean(self, *args, **kwargs):
        if self.cta_madre in self.arbol_de_subcuentas():
            raise errors.ErrorDependenciaCircular(
                f'Cuenta madre {self.cta_madre.nombre.capitalize()} está '
                f'entre las subcuentas de {self.nombre.capitalize()} o entre '
                f'las de una de sus subcuentas'
            )
        super().clean(*args, **kwargs)

    def manejar_cambios(self):
        if self._state.adding:
            return
        vieja = CuentaAcumulativa.tomar(pk=self.pk)
        if self.fecha_conversion != vieja.fecha_conversion:
            for mov in self.movs_conversion():
                mov.fecha = self.fecha_conversion
                mov.save()

    def save(self, *args, **kwargs):
        self.manejar_cambios()
        super().save(*args, **kwargs)

    def movs(self, order_by='fecha'):
        """ Devuelve movimientos propios y de sus subcuentas
            ordenados por fecha."""
        result = super().movs(order_by=order_by)
        for sc in self.subcuentas.all():
            result = result | sc.movs(order_by=order_by)
        return result.order_by(order_by)

    def movs_conversion(self) -> models.QuerySet:
        return models.QuerySet()

    def agregar_subcuenta(self, nombre, slug, titular=None):
        titular = titular or self.titular
        Cuenta.crear(nombre, slug, cta_madre=self, titular=titular)
