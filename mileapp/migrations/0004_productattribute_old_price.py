# Generated by Django 5.0.2 on 2024-03-26 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mileapp', '0003_wishlistitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='productattribute',
            name='old_price',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
