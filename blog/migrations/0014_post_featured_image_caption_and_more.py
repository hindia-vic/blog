# Generated by Django 5.1.6 on 2025-05-29 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0013_comment_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='featured_image_caption',
            field=models.CharField(blank=True, help_text='Optional caption for the featured image', max_length=200),
        ),
        migrations.AlterField(
            model_name='post',
            name='featured_image',
            field=models.ImageField(blank=True, help_text='Featured image for the post (1200x630px recommended)', null=True, upload_to='posts/%Y/%m/%d/'),
        ),
    ]
