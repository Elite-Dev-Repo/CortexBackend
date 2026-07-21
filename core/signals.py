from core import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import OTP, User
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
import os

@receiver(post_save, sender=User)
def create_otp(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            return
        instance.is_active=False
        instance.save()
        otp = OTP.objects.create(user=instance, expires_at=timezone.now() + timedelta(minutes=10))


@receiver(post_save, sender=OTP)
def send_otp_email(sender, instance, created, **kwargs):
    if created:
        send_mail(
            subject='Verify your email',
            message=f'Your OTP is {instance.otp}',
            from_email=os.getenv('EMAIL_HOST_USER'),
            recipient_list=[instance.user.email],
            fail_silently=False,
        )