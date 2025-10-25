# Generated manually for MusicBanner products and pricing fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pixelbazar', '0012_contact_is_read'),
    ]

    operations = [
        migrations.AddField(
            model_name='musicbanner',
            name='products',
            field=models.ManyToManyField(blank=True, related_name='music_banners', to='pixelbazar.product'),
        ),
        migrations.AddField(
            model_name='musicbanner',
            name='price_range_min',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='musicbanner',
            name='price_range_max',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='musicbanner',
            name='discount_text',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]