# Generated by Django 3.2 on 2022-05-08 12:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0029_rename_importe_saldo__importe'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cuenta',
            name='_saldo',
        ),
    ]