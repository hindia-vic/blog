# Generated by Django 5.1.6 on 2025-03-26 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_trigram_ext'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='featured_image',
            field=models.ImageField(blank=True, null=True, upload_to='posts/%Y/%m/%d/'),
        ),
    ]
