# Generated manually for Contact is_read field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pixelbazar', '0011_product_flash_sale_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]