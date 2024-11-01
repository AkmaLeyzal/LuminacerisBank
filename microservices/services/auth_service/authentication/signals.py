# auth_service/authentication/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
from .models import User

@receiver(pre_save, sender=User)
def hash_password(sender, instance, **kwargs):
    # Only hash password if it's been changed
    if instance._state.adding or instance.has_changed('password'):
        instance.password = make_password(instance.password)