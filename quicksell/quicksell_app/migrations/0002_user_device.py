# Generated by Django 3.1.7 on 2021-03-29 22:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fcm_django', '0005_auto_20170808_1145'),
        ('quicksell_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='device',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fcm_django.fcmdevice'),
        ),
    ]
