# Generated by Django 5.0.6 on 2024-08-21 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraddress',
            name='postal_code',
            field=models.IntegerField(),
        ),
    ]
