# Generated by Django 3.2 on 2022-04-23 13:44

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0025_auto_20220423_1336'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuenta',
            name='fecha_creacion',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
