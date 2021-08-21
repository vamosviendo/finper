# Generated by Django 3.2 on 2021-07-01 23:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diario', '0004_auto_20210519_2336'),
    ]

    operations = [
        migrations.CreateModel(
            name='CuentaAcumulativa',
            fields=[
                ('cuenta_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='diario.cuenta')),
            ],
            options={
                'abstract': False,
            },
            bases=('diario.cuenta',),
        ),
        migrations.CreateModel(
            name='CuentaInteractiva',
            fields=[
                ('cuenta_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='diario.cuenta')),
            ],
            options={
                'abstract': False,
            },
            bases=('diario.cuenta',),
        ),
        migrations.AlterModelOptions(
            name='movimiento',
            options={'ordering': ('fecha',)},
        ),
    ]