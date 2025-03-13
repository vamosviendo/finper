from __future__ import annotations

from datetime import date
from typing import Optional, Self, List, Sequence, Set, Any, TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse

from diario.consts import *
from diario.fields import CaseInsensitiveCharField
from diario.models.dia import Dia
from diario.models.moneda import Moneda
from diario.models.movimiento import Movimiento
from diario.models.saldo import Saldo
from diario.models.titular import Titular
from diario.settings_app import MONEDA_BASE, TITULAR_PRINCIPAL
from diario.utils.utils_moneda import id_moneda_base
from utils import errors
from utils.iterables import remove_duplicates
from utils.tiempo import Posicion
from vvmodel.managers import PolymorphManager
from vvmodel.models import PolymorphModel


alfaminusculas = RegexValidator(
    r'^[0-9a-z_\-]*$', 'Solamente caracteres alfanuméricos y guiones')


def signo(condicion):
    return 1 if condicion else -1


class CuentaManager(PolymorphManager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class Cuenta(PolymorphModel):
    nombre = CaseInsensitiveCharField(max_length=100, unique=True)
    slug = models.CharField(
        max_length=20, unique=True, validators=[alfaminusculas])
    cta_madre = models.ForeignKey(
        'CuentaAcumulativa',
        related_name='subcuentas',
        null=True, blank=True,
        on_delete=models.CASCADE,
    )
    fecha_creacion = models.DateField(default=date.today)
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, null=True, blank=True)

    objects = CuentaManager()

    class Meta:
        ordering = ('nombre', )

    @classmethod
    def crear(cls, nombre: str, slug: str, cta_madre: 'CuentaAcumulativa' = None, finalizar=False, **kwargs) -> CuentaInteractiva:
        """

        @rtype: object
        """
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

    def natural_key(self):
        return (self.slug, )

    @property
    def ctaname(self):
        return self.slug

    @property
    def es_interactiva(self) -> bool:
        return str(self.content_type) == 'diario | cuenta interactiva'

    @property
    def es_acumulativa(self) -> bool:
        return str(self.content_type) == 'diario | cuenta acumulativa'

    @property
    def es_cuenta_credito(self) -> bool:
        return self.has_not_none_attr('contracuenta')

    def saldo(
            self,
            movimiento: Movimiento = None,
            moneda: Moneda = None,
            compra: bool = False) -> float:

        fecha = movimiento.fecha if movimiento else date.today()
        cotizacion = self.moneda.cotizacion_en_al(moneda, fecha, compra) if moneda else 1

        try:
            return round(Saldo.tomar(cuenta=self, movimiento=movimiento).importe * cotizacion, 2)
        except AttributeError:  # movimiento is None
            try:
                return round(self.ultimo_saldo.importe * cotizacion, 2)
            except AttributeError:  # No hay saldos
                return 0
        except Saldo.DoesNotExist:  # Se pasó movimiento pero no hay saldos
            return 0

    @property
    def cotizacion(self) -> float:
        return self.moneda.cotizacion

    def recalcular_saldos_entre(self,
                                pos_desde: Posicion = Posicion(orden_dia=0),
                                pos_hasta: Posicion = Posicion(orden_dia=100000000)):
        pos_hasta.fecha = pos_hasta.fecha or date.today()
        pos_hasta.orden_dia = pos_hasta.orden_dia or 100000000

        saldos = Saldo.posteriores_a(self, pos_desde, inclusive_od=True) & \
                 Saldo.anteriores_a(self, pos_hasta, inclusive_od=True)
        for saldo in saldos:
            try:
                saldo.importe = saldo.anterior().importe
            except AttributeError:  # saldo.anterior() is None
                saldo.importe = 0
            saldo.importe += saldo.movimiento.importe_cta_entrada if saldo.viene_de_entrada \
                else saldo.movimiento.importe_cta_salida
            saldo.save()

    @property
    def ultimo_saldo(self) -> Saldo:
        return self.saldo_set.last()

    def clean_fields(self, exclude: Sequence[str] = None):
        self._pasar_slug_a_minuscula()

        if self.moneda is None:
            try:
                self.moneda = Moneda.tomar(pk=id_moneda_base())
            except errors.ErrorMonedaBaseInexistente:
                self.moneda = Moneda.crear(
                    monname=MONEDA_BASE, nombre=MONEDA_BASE
                )

        super().clean_fields(exclude=exclude)

    def clean(self):
        self.impedir_cambio('cta_madre')
        self.impedir_cambio('moneda')
        self._chequear_incongruencias_de_clase()
        self._verificar_fecha_creacion()

    def delete(self, *args, **kwargs):
        if self.saldo() != 0:
            raise errors.SaldoNoCeroException
        super().delete(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse('cuenta', args=[self.slug])

    def movs_directos(self) -> models.QuerySet[Movimiento]:
        """ Devuelve entradas y salidas de la cuenta sin los de sus subcuentas
        """
        return self.entradas.all() | self.salidas.all()

    def movs_directos_en_fecha(self, dia: Dia) -> models.QuerySet[Movimiento]:
        """ Devuelve movimientos directos de la cuenta en una fecha dada"""
        return self.movs_directos().filter(dia=dia)

    def movs(self, order_by: list[str] = None) -> models.QuerySet[Movimiento]:
        """ Devuelve movimientos propios y de sus subcuentas
            ordenados por fecha y orden_dia.
            Antes de protestar que devuelve lo mismo que movs_directos()
            tener en cuenta que está sobrescrita en CuentaAcumulativa
            """
        if order_by is None:
            order_by = ['dia', 'orden_dia']
        return self.movs_directos().order_by(*order_by)

    def dias(self) -> models.QuerySet[Dia]:
        """ Devuelve días en los que haya movimientos propios y de sus subcuentas
            ordenados por fecha.
        """
        fechas = [mov.dia.fecha for mov in self.movs()]
        return Dia.filtro(fecha__in=fechas)

    def movs_en_fecha(self, dia: Dia) -> models.QuerySet[Movimiento]:
        """ Devuelve movimientos propios y de sus subcuentas en una fecha dada.
        Ver comentario anterior."""
        return self.movs().filter(dia=dia)

    def cantidad_movs(self) -> int:
        return self.entradas.count() + self.salidas.count()

    def total_movs(self) -> float:
        """ Devuelve suma de los importes de los movimientos de la cuenta"""
        total_entradas = sum([x.importe_cta_entrada for x in self.entradas.all()])
        total_salidas = sum([x.importe_cta_salida for x in self.salidas.all()])

        return round(total_entradas + total_salidas, 2)

    def fecha_ultimo_mov_directo(self) -> Optional[date]:
        try:
            return self.movs_directos().order_by('dia').last().fecha
        except AttributeError:
            return None

    def tiene_madre(self) -> bool:
        return self.cta_madre is not None

    def tomar_del_slug(self) -> Self:
        return Cuenta.tomar_o_nada(slug=self.slug)

    def hermanas(self) -> Optional[models.QuerySet[Self]]:
        if self.cta_madre:
            return self.cta_madre.subcuentas.all().exclude(pk=self.pk)
        return None

    def ancestros(self) -> list[Self]:
        cta_madre = self.cta_madre
        lista_ancestros = []

        while cta_madre:
            lista_ancestros.append(cta_madre)
            cta_madre = cta_madre.cta_madre

        return lista_ancestros

    # Métodos protegidos

    def _pasar_slug_a_minuscula(self):
        if self.slug:
            self.slug = self.slug.lower()

    def _chequear_incongruencias_de_clase(self):
        if self.es_acumulativa and self.como_subclase().subcuentas.count()== 0:
            raise errors.ErrorTipo(errors.CUENTA_ACUMULATIVA_SIN_SUBCUENTAS)
        if self.cta_madre and self.cta_madre.es_interactiva:
            raise errors.ErrorTipo(f'Cuenta interactiva "{self.cta_madre }" '
                                   f'no puede ser madre')

    def _verificar_fecha_creacion(self):
        if self.tiene_madre() and self.fecha_creacion < self.cta_madre.fecha_conversion:
            raise errors.ErrorFechaAnteriorACuentaMadre


class CuentaInteractiva(Cuenta):

    _contracuenta = models.OneToOneField(
        'diario.CuentaInteractiva',
        null=True, blank=True,
        related_name='_cuentacontra',
        on_delete=models.CASCADE
    )
    titular = models.ForeignKey('diario.Titular',
                                related_name='cuentas',
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True)

    @classmethod
    def crear(cls, nombre: str, slug: str, cta_madre: Cuenta = None, saldo: float = None, **kwargs) -> Self:

        cuenta_nueva = super().crear(nombre=nombre, slug=slug,
                                     cta_madre=cta_madre, finalizar=True,
                                     **kwargs)

        if saldo and float(saldo) != 0.0:
            Movimiento.crear(
                concepto=f'Saldo inicial de {cuenta_nueva.nombre}',
                importe=saldo,
                cta_entrada=cuenta_nueva,
                fecha=cuenta_nueva.fecha_creacion,
                moneda=cuenta_nueva.moneda,
            )

        return cuenta_nueva

    def clean(self):
        super().clean()
        self._corregir_titular_vacio()
        self.impedir_cambio('titular')
        self._verificar_fecha_creacion_interactiva()

    @property
    def contracuenta(self) -> Optional[Self]:
        """ En cuentas crédito, devuelve la cuenta crédito del titular
            de la cuenta contrapartida en el movimiento de crédito, o viceversa.
            En cuentas normales, devuelve None
        """
        if self._contracuenta:
            return self._contracuenta
        try:
            return self._cuentacontra
        except CuentaInteractiva._cuentacontra.RelatedObjectDoesNotExist:
            # no es cuenta crédito
            return None

    def corregir_saldo(self):
        self.recalcular_saldos_entre(Posicion(self.fecha_creacion))

    def agregar_mov_correctivo(self) -> Optional[Movimiento]:
        if self.saldo_ok():
            return None
        saldo = self.ultimo_saldo
        importe = saldo.importe
        mov = Movimiento(concepto='Movimiento correctivo')
        mov.importe = self.saldo() - self.total_movs()
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

    def saldo_ok(self) -> bool:
        return self.saldo() == self.total_movs()

    def dividir_entre(
            self,
            *subcuentas: dict[str, str | float] | Sequence[str | float],
            fecha: date = None
    ) -> List[Self]:
        fecha = fecha or date.today()

        if fecha < self.fecha_creacion:
            raise errors.ErrorFechaCreacionPosteriorAConversion

        try:
            if fecha < self.fecha_ultimo_mov_directo():
                raise errors.ErrorMovimientoPosteriorAConversion
        except TypeError:
            pass

        if not self.saldo_ok():
            raise ValidationError(
                f'Saldo de cuenta "{self.nombre}" no coincide con sus movimientos. '
                f'Saldo: {self.saldo()} - Total movimientos: {self.total_movs()}'
            )

        cuentas_limpias = self._ajustar_subcuentas(subcuentas)

        movimientos_incompletos = self._vaciar_saldo(cuentas_limpias, fecha)

        cta_madre = self._convertirse_en_acumulativa(fecha)

        cuentas_creadas = self._generar_subcuentas(
            cuentas_limpias, movimientos_incompletos, cta_madre, fecha
        )
        return cuentas_creadas

    def dividir_y_actualizar(self, *subcuentas: Sequence[dict | Sequence | int], fecha: date = None) -> Cuenta | CuentaAcumulativa:
        self.dividir_entre(*subcuentas, fecha=fecha)
        return self.tomar_del_slug()

    # Protected

    def _ajustar_subcuentas(self, subcuentas: Sequence[dict | Sequence]) -> List[dict]:
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

                dic_subcuenta['saldo'] = self.saldo() - total_otras_subcuentas

            # Si saldo no es float, convertir
            dic_subcuenta['saldo'] = float(dic_subcuenta['saldo'])
            subcuentas_limpias.append(dic_subcuenta)

        # En este punto suma saldos subcuentas debe ser igual a self.saldo()
        suma_saldos_subcuentas = sum([x['saldo'] for x in subcuentas_limpias])
        if suma_saldos_subcuentas != self.saldo():
            raise errors.ErrorDeSuma(
                f"Suma errónea. Saldos de subcuentas "
                f"deben sumar {self.saldo():.2f} (suman {suma_saldos_subcuentas})"
            )

        return subcuentas_limpias

    @staticmethod
    def _asegurar_dict(subcuenta: Sequence | dict) -> dict:
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

    def _convertirse_en_acumulativa(self, fecha: date = None) -> CuentaAcumulativa:
        fecha = fecha or date.today()
        titular = self.titular
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
        cuenta_acumulativa.titular_original = titular
        cuenta_acumulativa.save()
        return cuenta_acumulativa

    def _vaciar_saldo(self, cuentas_limpias: List[dict], fecha: date = None) -> List[Movimiento]:
        fecha = fecha or date.today()
        movimientos_incompletos = []

        for subcuenta in cuentas_limpias:
            saldo = subcuenta.pop('saldo')
            campo_cuenta, contracampo = (
                CTA_ENTRADA, CTA_SALIDA
            ) if saldo >= 0 else (
                CTA_SALIDA, CTA_ENTRADA
            )
            saldo = abs(saldo)
            dict_cuenta = {contracampo: self}

            try:
                movimientos_incompletos.append(Movimiento.crear(
                    fecha=fecha,
                    concepto="Traspaso de saldo",
                    detalle=f'Saldo pasado por {self.nombre.capitalize()} ' 
                            f'a nueva subcuenta '
                            f'{subcuenta["nombre"].lower().capitalize()}',
                    importe=saldo,
                    esgratis=subcuenta.pop('esgratis', False),
                    convierte_cuenta=campo_cuenta,
                    moneda=self.moneda,
                    **dict_cuenta
                ))
            except errors.ErrorImporteCero:
                # Si el saldo de la subcuenta es 0, no generar movimiento
                movimientos_incompletos.append(None)

        return movimientos_incompletos

    @staticmethod
    def _generar_subcuentas(
            cuentas_limpias: List[dict],
            movimientos_incompletos: List[Movimiento],
            cta_madre: CuentaAcumulativa,
            fecha: date
    ) -> List[CuentaInteractiva]:

        cuentas_creadas = list()

        for i, subcuenta in enumerate(cuentas_limpias):
            cuentas_creadas.append(
                Cuenta.crear(
                    **subcuenta,
                    cta_madre=cta_madre,
                    fecha_creacion=fecha,
                    moneda=cta_madre.moneda,
                )
            )

            if movimientos_incompletos[i] is not None:
                if movimientos_incompletos[i].cta_salida is not None:
                    movimientos_incompletos[i].cta_entrada = cuentas_creadas[i]
                elif movimientos_incompletos[i].cta_entrada is not None:
                    movimientos_incompletos[i].cta_salida = cuentas_creadas[i]
                movimientos_incompletos[i].save()

        return cuentas_creadas

    def _corregir_titular_vacio(self):
        if self.titular is None:
            try:
                titular = Titular.tomar(titname=TITULAR_PRINCIPAL)
            except Titular.DoesNotExist:
                raise errors.ErrorTitularPorDefectoInexistente
            self.titular = titular

    def _verificar_fecha_creacion_interactiva(self):
        if self.fecha_creacion < self.titular.fecha_alta:
            raise errors.ErrorFechaAnteriorAAltaTitular(
                message=f'Fecha de creación de cuenta "{self.nombre}" ({self.fecha_creacion}) '
                        f'anterior a fecha de alta de titular "{self.titular.nombre}" '
                        f'({self.titular.fecha_alta})'
            )


class CuentaAcumulativa(Cuenta):

    fecha_conversion = models.DateField()
    titular_original = models.ForeignKey('diario.Titular',
                                related_name='ex_cuentas',
                                on_delete=models.CASCADE,)

    @property
    def titulares(self) -> List[Titular]:
        titulares = list()
        subcuentas = list(self.subcuentas.all())

        for subcuenta in subcuentas:
            if subcuenta.es_interactiva:
                titulares.append(subcuenta.titular)
            else:
                titulares += subcuenta.titulares

        return remove_duplicates(titulares)

    def arbol_de_subcuentas(self) -> Set[Cuenta]:
        todas_las_subcuentas = set(self.subcuentas.all())
        for cuenta in self.subcuentas.all():
            if cuenta.es_acumulativa:
                todas_las_subcuentas.update(cuenta.arbol_de_subcuentas())
        return todas_las_subcuentas

    def saldo(
            self,
            movimiento: Movimiento = None,
            moneda: Moneda = None,
            compra: bool = False,) -> float:

        fecha = movimiento.fecha if movimiento else date.today()
        cotizacion = self.moneda.cotizacion_en_al(moneda, fecha, compra) if moneda else 1

        if movimiento:
            slugs_ctas_mov = [
                movimiento.cta_entrada.slug if movimiento.cta_entrada else None,
                movimiento.cta_salida.slug if movimiento.cta_salida else None,
            ]
            if self.slug in slugs_ctas_mov: # La cuenta participó del movimiento cuando aún era interactiva
                return round(Saldo.tomar(cuenta=self, movimiento=movimiento).importe * cotizacion, 2)
        return round(
            sum([subc.saldo(movimiento=movimiento) for subc in self.subcuentas.all()]) * cotizacion,
            2
        )

    def clean(self):
        super().clean()
        self._verificar_fechas()

    def manejar_cambios(self):
        if self._state.adding:
            return
        vieja = CuentaAcumulativa.tomar(pk=self.pk)
        if self.fecha_conversion != vieja.fecha_conversion:
            for mov in self.movs_conversion():
                if mov.fecha != self.fecha_conversion:
                    mov.fecha = self.fecha_conversion
                    mov.save()

    def save(self, *args, **kwargs):
        self.manejar_cambios()
        super().save(*args, **kwargs)

    def movs(self, order_by: list[str] = None) -> models.QuerySet[Movimiento]:
        """ Devuelve movimientos propios y de sus subcuentas
            ordenados por fecha y orden_dia."""
        if order_by is None:
            order_by = ['dia', 'orden_dia']
        result = super().movs(order_by=order_by)
        for sc in self.subcuentas.all():
            result = result | sc.movs(order_by=order_by)
        return result.order_by(*order_by)

    def movs_conversion(self) -> models.QuerySet[Movimiento]:
        return self.movs().filter(convierte_cuenta__in=campos_cuenta)

    def movs_no_conversion(self) -> models.QuerySet[Movimiento]:
        return self.movs().filter(convierte_cuenta=None)

    def agregar_subcuenta(self, nombre: str, slug: str, titular: Titular, fecha: date = None) -> CuentaInteractiva:
        return Cuenta.crear(
            nombre=nombre,
            slug=slug,
            cta_madre=self,
            titular=titular,
            fecha_creacion=fecha or date.today(),
            moneda=self.moneda,
        )

    def _verificar_fechas(self):
        for titular in self.titulares:
            if self.fecha_creacion < titular.fecha_alta:
                raise errors.ErrorFechaAnteriorAAltaTitular(
                    f"Fecha de creación de la cuenta {self.nombre} "
                    f"({self.fecha_creacion}) posterior a la "
                    f"fecha de alta de uno de sus titulares "
                    f"({titular} - {titular.fecha_alta})"
                )

        if self.fecha_creacion > self.fecha_conversion:
            raise errors.ErrorFechaCreacionPosteriorAConversion(
                f"La fecha de creación de la cuenta {self.nombre} "
                f"({self.fecha_creacion}) no puede ser posterior a su "
                f"fecha de conversión ({self.fecha_conversion})"
            )

        for cuenta in self.subcuentas.all():
            if self.fecha_conversion > cuenta.fecha_creacion:
                raise errors.ErrorFechaConversionPosteriorACreacionSubcuenta(
                    f"La fecha de conversión de la cuenta {self.nombre} "
                    f"({self.fecha_conversion}) no puede ser posterior a la "
                    f"fecha de creación de su subcuenta {cuenta.nombre} "
                    f"({cuenta.fecha_creacion})"
                )

        movs_normales = self.movs_no_conversion()
        fecha_ultimo_mov_normal = max([m.fecha for m in movs_normales]) \
            if movs_normales.count() > 0 else date(1, 1, 1)
        if self.fecha_conversion < fecha_ultimo_mov_normal:
            raise errors.ErrorMovimientoPosteriorAConversion(
                f'La fecha de conversión no puede ser anterior a la del '
                f'último movimiento de la cuenta ({fecha_ultimo_mov_normal})'
            )
