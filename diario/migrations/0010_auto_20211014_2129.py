# Generated by Django 3.2 on 2021-10-14 21:29

import diario.models.titular
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0009_remove_cuenta_opciones'),
    ]

    operations = [
        migrations.CreateModel(
            name='Titular',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titname', models.CharField(max_length=100, unique=True)),
                ('nombre', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='cuentainteractiva',
            name='titular',
            field=models.ForeignKey(blank=True, default=diario.models.titular.Titular.por_defecto, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cuentas', to='diario.titular'),
        ),
    ]
