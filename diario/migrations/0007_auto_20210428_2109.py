# Generated by Django 3.2 on 2021-04-28 21:09

import diario.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0006_cuenta_saldo'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuenta',
            name='slug',
            field=models.CharField(default='', max_length=4, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='movimiento',
            name='fecha',
            field=models.DateField(default=diario.models.hoy),
        ),
    ]
