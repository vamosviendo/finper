from django.contrib import admin

from diario.models import Movimiento


class MovimientoAdmin(admin.ModelAdmin):
    fields = [
        'fecha', 'orden_dia', 'concepto', 'detalle', '_importe',
        'cta_entrada', 'cta_salida', 'id_contramov',
        'convierte_cuenta', 'es_automatico'
    ]


admin.site.register(Movimiento, MovimientoAdmin)
