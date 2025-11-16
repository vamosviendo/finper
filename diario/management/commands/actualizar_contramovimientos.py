from django.core.management import BaseCommand

from diario.models import Movimiento


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for mov in Movimiento.excepto(id_contramov=None):
            contramov = Movimiento.tomar(id=mov.id_contramov)
            print(f"Actualizando contramov {contramov.sk}: {mov.concepto}")
            contramov.detalle = contramov.concepto
            contramov.concepto = mov.concepto
            contramov.save()
