# Generated by Django 4.2.1 on 2023-06-23 23:15

import diario.models.titular
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0032_alter_movimiento_convierte_cuenta'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cuenta',
            name='titular',
        ),
        migrations.AddField(
            model_name='cuentainteractiva',
            name='titular',
            field=models.ForeignKey(blank=True, default=diario.models.titular.Titular.por_defecto, on_delete=django.db.models.deletion.CASCADE, related_name='cuentas', to='diario.titular'),
        ),
    ]