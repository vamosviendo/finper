# Generated by Django 3.2 on 2021-12-24 00:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0020_alter_cuenta_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuenta',
            name='nombre',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
