from django.apps import AppConfig


class PixelbazarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pixelbazar'
    
    def ready(self):
        from django.contrib import admin
        admin.site.site_header = 'PixelBazar Admin Panel'
        admin.site.site_title = 'PixelBazar Admin'
        admin.site.index_title = 'Welcome to PixelBazar Administration'