# Generated by Django 4.2.1 on 2024-08-25 23:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0002_remove_moneda_cotizacion_cotizacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimiento',
            name='_cotizacion',
            field=models.FloatField(default=0.0),
        ),
    ]
