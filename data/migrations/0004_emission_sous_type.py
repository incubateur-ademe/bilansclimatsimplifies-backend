# Generated by Django 3.2.8 on 2021-12-03 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0003_post_total_integer'),
    ]

    operations = [
        migrations.AddField(
            model_name='emission',
            name='sous_type',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='détail'),
        ),
    ]