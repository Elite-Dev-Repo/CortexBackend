import uuid

# pyrefly: ignore [missing-import]
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import secrets
# Create your models here.


class UserModelManager(BaseUserManager):
    """Manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)

        user = self.model( email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if not password:
            raise ValueError('Superuser must have a password.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'
    
    objects = UserModelManager()


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, default=secrets.token_hex(3))
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP: {self.otp} - {self.user.username}"



class Workspace(models.Model):
    WORKSPACE_TYPE = [
        ('PERSONAL', "PERSONAL"),
        ('TEAM', "TEAM")
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    workspace_type = models.CharField(max_length=20, choices=WORKSPACE_TYPE, default="PERSONAL")
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace')

    def __str__(self):
        return f"Workspace: {self.name} - {self.user.username}"


class TeamMember(models.Model):
    ROLES = [
        ("ADMIN","ADMIN"),
        ("MEMBER", "MEMBER"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default="MEMBER")

    def save(self, *args, **kwargs):
        if self.user == self.workspace.owner:
            self.role="ADMIN"
        else:
            self.role="MEMBER"
            super.save(*args, **kwargs)

def _default_position():
    return {"x": 0, "y": 0}


class Project(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="pending")
    position = models.JSONField(default=_default_position)

    def __str__(self):
        return f"Project: {self.name} - {self.workspace.name}"


class Feature(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    tags = models.JSONField(default=list)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="pending")
    position = models.JSONField(default=_default_position)

    def __str__(self):
        return f"Feature: {self.name} - {self.project.name}"


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="pending")
    position = models.JSONField(default=_default_position)

    def __str__(self):
        return f"Task: {self.name} - {self.feature.name}"




class Edge(models.Model):
    id = models.CharField(max_length=40, primary_key=True)
    animated= models.BooleanField(default=True)
    source = models.CharField(max_length=40)
    target = models.CharField(max_length=40)
    targetHandle = models.CharField(max_length=40)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='edge')
