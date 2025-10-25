# Generated manually for Product category choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pixelbazar', '0013_musicbanner_products_pricing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_category',
            field=models.CharField(blank=True, choices=[('phones', 'Phones'), ('laptops', 'Laptops'), ('speakers', 'Speakers'), ('headphones', 'Headphones'), ('cameras', 'Cameras'), ('music', 'Music'), ('electronics', 'Electronics')], max_length=50, null=True),
        ),
    ]