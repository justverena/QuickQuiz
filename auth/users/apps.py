from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.contrib.auth.management import create_permissions


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    
    def ready(self):
        post_migrate.disconnect(create_permissions, dispatch_uid="django.contrib.auth.management.create_permissions")
