# Generated by Django 3.2.10 on 2021-12-17 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0006_alter_report_region'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='mode',
            field=models.CharField(choices=[('manuel', 'Déclaré'), ('auto', 'Calculé')], default='auto', max_length=10, verbose_name='mode de publication'),
        ),
    ]