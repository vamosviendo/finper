# Generated by Django 4.2.1 on 2025-04-10 22:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0010_rename_sk_moneda__sk'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cuenta',
            old_name='sk',
            new_name='_sk',
        ),
    ]
