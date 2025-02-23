# Generated by Django 4.2.5 on 2024-05-07 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moops_app', '0009_review'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeroSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heading', models.CharField(max_length=200)),
                ('paragraph', models.TextField()),
                ('background_image', models.ImageField(upload_to='hero_images/')),
            ],
        ),
    ]
