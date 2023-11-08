# Generated by Django 4.2.1 on 2023-11-08 17:26

import diario.utils.utils_moneda
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0003_moneda'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuenta',
            name='moneda',
            field=models.ForeignKey(default=diario.utils.utils_moneda.moneda_base, on_delete=django.db.models.deletion.CASCADE, to='diario.moneda'),
        ),
    ]
