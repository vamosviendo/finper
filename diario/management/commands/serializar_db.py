from io import StringIO

from django.core.management import BaseCommand, call_command


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        serialized_db = StringIO()
        call_command('dumpdata', 'diario', '--natural-foreign', stdout=serialized_db)

        with open('db_full.json', 'w') as db_full:
            db_full.write(serialized_db.getvalue())
