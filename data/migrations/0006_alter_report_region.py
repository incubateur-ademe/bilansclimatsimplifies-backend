# Generated by Django 3.2.10 on 2021-12-17 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0005_verbose_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='region',
            field=models.CharField(blank=True, choices=[('01', 'Guadeloupe'), ('02', 'Martinique'), ('03', 'Guyane'), ('04', 'La Réunion'), ('06', 'Mayotte'), ('11', 'Île-de-France'), ('24', 'Centre-Val de Loire'), ('27', 'Bourgogne-Franche-Comté'), ('28', 'Normandie'), ('32', 'Hauts-de-France'), ('44', 'Grand Est'), ('52', 'Pays de la Loire'), ('53', 'Bretagne'), ('75', 'Nouvelle-Aquitaine'), ('76', 'Occitanie'), ('84', 'Auvergne-Rhône-Alpes'), ('93', "Provence-Alpes-Côte d'Azur"), ('94', 'Corse')], max_length=4, null=True, verbose_name='code région'),
        ),
    ]