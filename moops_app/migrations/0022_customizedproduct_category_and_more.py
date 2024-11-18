# Generated by Django 4.2.5 on 2024-10-24 17:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('moops_app', '0021_ingredients_categorys_alter_ingredients_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='customizedproduct',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='moops_app.category'),
        ),
        migrations.AddField(
            model_name='customizedproduct',
            name='product_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='moops_app.producttype'),
        ),
    ]
