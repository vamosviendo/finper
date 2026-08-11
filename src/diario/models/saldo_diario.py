from __future__ import annotations
from typing import TYPE_CHECKING, Self, Iterable, cast

from django.db import models, transaction

from vvmodel.models import MiModel

if TYPE_CHECKING:
    from diario.models import Movimiento, Cuenta, Dia


class SaldoDiario(MiModel):
    cuenta = models.ForeignKey('diario.Cuenta', on_delete=models.CASCADE)
    dia = models.ForeignKey('diario.Dia', on_delete=models.CASCADE)
    _importe = models.FloatField()
    sk = models.CharField(max_length=25, null=True, blank=True, unique=True)

    class Meta:
        unique_together = ['cuenta', 'dia']
        ordering = ['dia']

    def __str__(self):
        return f"{self.cuenta} al {self.dia}: {self.importe}"

    @property
    def importe(self) -> float:
        return self._importe

    @importe.setter
    def importe(self, value: float):
        self._importe = round(value, 2)

    @classmethod
    def anterior_a(cls, cuenta: Cuenta, dia: Dia):
        return cls.filtro(cuenta_id=cuenta.pk, dia__fecha__lt=dia.fecha).last()

    @classmethod
    def calcular(cls, mov: Movimiento, sentido: str | None = None):
        if sentido is None:
            if mov.cta_entrada is None:
                sentido = "salida"
            elif mov.cta_salida is None:
                sentido = "entrada"
            else:
                raise ValueError('En un movimiento de traspaso debe especificarse argumento "sentido"')

        if sentido.startswith("cta_"):
            sentido = sentido[4:]
        if sentido not in ("entrada", "salida"):
            raise ValueError(
                'Los valores aceptados para arg "sentido" son "entrada", "cta_entrada", "salida", "cta_salida"'
            )

        cuenta = getattr(mov, f"cta_{sentido}")
        importe_mov = mov.importe_cta(sentido)

        try:
            saldo_diario = cls.tomar(cuenta=cuenta, dia=mov.dia)
            saldo_diario.importe += importe_mov
            saldo_diario.clean_save()
        except cls.DoesNotExist:
            try:
                importe = cls.anterior_a(cuenta=cuenta, dia=mov.dia).importe + importe_mov
            except AttributeError:  # No hay saldo diario anterior
                importe = importe_mov
            saldo_diario = cls.crear(cuenta=cuenta, dia=mov.dia, importe=importe)

        return saldo_diario

    def anterior(self):
        return SaldoDiario.anterior_a(cuenta=self.cuenta, dia=self.dia)

    @transaction.atomic
    def eliminar(self):
        importe = self.importe
        try:
            importe_anterior = self.anterior().importe
        except AttributeError:
            importe_anterior = 0
        self.delete()
        self._actualizar_posteriores(importe_anterior-importe)

    def clean_save(
            self, exclude=None, validate_unique=True, validate_constraints=True,
            force_insert=False, force_update=False, using=None, update_fields=None,
            actualizar_posteriores=True
    ):
        super().full_clean(exclude, validate_unique, validate_constraints)
        self.save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields,
                  actualizar_posteriores=actualizar_posteriores)

    @transaction.atomic
    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None,
            actualizar_posteriores=True
    ):
        # Generar sk si no existe
        if self.sk is None:
            self.sk = f"{self.dia.sk}{self.cuenta.sk}"

        if self._state.adding:
            try:
                importe_anterior = self.anterior().importe
                importe = self.importe - importe_anterior
            except AttributeError:  # No hay movimiento anterior.
                importe = self.importe
            self._actualizar_posteriores(importe)

        else:
            if self.cambia_campo("_importe"):
                importe_guardado = self.tomar_de_bd().importe
                importe = self.importe - importe_guardado
                if actualizar_posteriores:
                    self._actualizar_posteriores(importe)

        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

    def tomar_de_bd(self) -> Self:
        return self.get_class().tomar_o_nada(cuenta=self.cuenta, dia=self.dia)

    @classmethod
    def saldos_cuentas(
            cls,
            cuentas: Iterable['Cuenta'],
            dia: Dia | None = None,
            movimiento: Movimiento | None = None) -> dict[int, float]:
        """ Devuelve {cuenta.pk: importe} para todos los pares cuenta/día.
            Usa 2 queries SQL totales sin importar la cantidad de cuentas o días."""
        if cuentas is None:
            return {}
        if dia is None and movimiento is None:
            return {}

        if movimiento and dia and movimiento.dia != dia:
            raise ValueError(
                f'El movimiento "{movimiento.concepto}" del {movimiento.dia} '
                f'no corresponde al día {dia}.'
            )

        cuentas = list(cuentas)
        if not cuentas:
            return {}

        dia_referencia = movimiento.dia if movimiento else dia
        return cls._calcular_saldos(
            cast(list, cuentas), dia_referencia, movimiento
        )

    # Métodos protegidos

    def _actualizar_posteriores(self, importe):
        for sd in SaldoDiario.filtro(cuenta=self.cuenta, dia__fecha__gt=self.dia.fecha):
            sd.importe += importe

            sd.clean_save(actualizar_posteriores=False)

    @classmethod
    def _calcular_saldos(
            cls,
            cuentas: list[Cuenta],
            dia: Dia | None,
            movimiento: Movimiento | None,
    ) -> dict[int, float]:
        from diario.models import Cuenta

        resultado = {}

        acumulativas = [c for c in cuentas if c.es_acumulativa]
        interactivas = [c for c in cuentas if c.es_interactiva]

        # 1. Batch de subcuentas para acumulativas
        if acumulativas:
            todas_las_subcuentas = list(
                Cuenta.filtro(cta_madre__in=acumulativas)
            )
            subcuentas_por_madre = {}
            for sc in todas_las_subcuentas:
                subcuentas_por_madre.setdefault(sc.cta_madre_id, []).append(sc)
        else:
            todas_las_subcuentas = []
            subcuentas_por_madre = {}

        # 2. Batch de SaldoDiario
        cuentas_a_buscar = interactivas + todas_las_subcuentas
        saldos_dia = cls._obtener_saldos_dia_batch(cuentas_a_buscar, dia)

        # 3. Batch de movimientos
        if movimiento:
            ajustes = cls._obtener_ajustes_movimiento_batch(cuentas_a_buscar, movimiento)
        else:
            ajustes = {}

        # 4. Asignar saldos a interactivas
        for c in interactivas:
            resultado[c.pk] = saldos_dia.get(c.pk, 0.0) - ajustes.get(c.pk, 0.0)

        # 5. Recursión para acumulativas
        for c in acumulativas:
            subcuentas = subcuentas_por_madre.get(c.pk, [])
            saldos_subcuentas = cls._calcular_saldos(subcuentas, dia, movimiento)
            resultado.update(saldos_subcuentas)
            pks_directas = {sc.pk for sc in subcuentas}
            # TODO: Esta distinción se hace porque incluimos el árbol de subcuentas
            #       en el resultado pero no debemos incluir más que las subcuentas
            #       directas en el cálculo del saldo de la cuenta acumulativa.
            #       Verificar si realmente es necesario incluir las subcuentas
            #       en el resultado. (Esto para un refactoring posterior una vez
            #       que hayamos comprobado que pasan todos los tests).
            resultado[c.pk] = sum(
                imp for pk, imp in saldos_subcuentas.items() if pk in pks_directas
            )

        return resultado

    @classmethod
    def _obtener_saldos_dia_batch(cls, cuentas, dia):
        if not cuentas:
            return {}

        saldos = cls.filtro(
            cuenta__in=cuentas,
            dia__fecha__lte=dia.fecha,
        ).order_by('cuenta_id', '-dia__fecha')
        resultado = {}
        vistos = set()
        for saldo in saldos:
            if saldo.cuenta_id not in vistos:
                resultado[saldo.cuenta_id] = saldo.importe
                vistos.add(saldo.cuenta_id)

        return resultado

    @classmethod
    def _obtener_ajustes_movimiento_batch(cls, cuentas, movimiento):
        from diario.models import Movimiento

        if not cuentas:
            return {}

        movs = Movimiento.filtro(
            dia=movimiento.dia,
            orden_dia__gt=movimiento.orden_dia
        ).select_related('cta_entrada', 'cta_salida')

        ajustes = {c.pk: 0.0 for c in cuentas}
        for mov in movs:
            if mov.cta_entrada_id in ajustes:
                ajustes[mov.cta_entrada_id] += mov.importe_cta_entrada
            if mov.cta_salida_id in ajustes:
                ajustes[mov.cta_salida_id] += mov.importe_cta_salida
        return ajustes
