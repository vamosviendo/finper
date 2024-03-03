import json

from django.core.management import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        with open('db_full.json', 'w') as db_full:
            json.dump([dict()], db_full)
