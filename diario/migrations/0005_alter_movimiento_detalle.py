# Generated by Django 3.2 on 2021-04-19 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0004_auto_20210419_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimiento',
            name='detalle',
            field=models.TextField(blank=True, null=True),
        ),
    ]
