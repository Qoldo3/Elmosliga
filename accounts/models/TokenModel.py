from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
from .Users import User


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "email_verification_tokens"
        indexes = [
            models.Index(fields=["token", "used"]),
        ]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save()

    @classmethod
    def create_token(cls, user):
        """Create a new token and delete any existing unused tokens"""
        cls.objects.filter(user=user, used=False).delete()
        return cls.objects.create(user=user)

    def __str__(self):
        return f"Verification token for {self.user.email}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_tokens"
        indexes = [
            models.Index(fields=["token", "used"]),
        ]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save()

    @classmethod
    def create_token(cls, user):
        """Create a new token and delete any existing unused tokens"""
        cls.objects.filter(user=user, used=False).delete()
        return cls.objects.create(user=user)

    def __str__(self):
        return f"Password reset token for {self.user.email}"