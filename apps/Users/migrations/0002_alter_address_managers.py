# Generated by Django 3.2 on 2021-07-15 06:15

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='address',
            managers=[
                ('object', django.db.models.manager.Manager()),
            ],
        ),
    ]
