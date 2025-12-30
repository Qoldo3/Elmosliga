from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from .models import User

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Create profile for all users (including superusers) when they are created"""
    if created:
        Profile.objects.create(user=instance)
        print(f"Profile created for {instance.email}")  # Debug log