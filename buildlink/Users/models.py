from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from trades.models import Trade, WorkerTrade



class User(AbstractUser):
    class Roles(models.TextChoices):
        WORKER = 'worker', _('Worker')
        OWNER = 'owner', _('Owner')
        COMPANY = 'company', _('Company')
        STUDENT = 'student', _('Student')
        ADMIN = 'admin', _('Admin')

    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=Roles.choices)
    full_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_license = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    verified = models.BooleanField(default=False)
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    national_id = models.OneToOneField(
        'NationalID',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="user"
    ) 

    REQUIRED_FIELDS = ['email', 'phone', 'role','NationalID']

    def __str__(self):
        return f"{self.full_name} ({self.role})"



class Portfolio(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio')
    image_url = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.status}"
    
    


class NationalID(models.Model):
      id_number = models.CharField(max_length=16, unique=True)
      full_name = models.CharField(max_length=100)
      dob = models.DateField()
      gender = models.CharField(max_length=10)

def __str__(self):
        return f"{self.full_name} - {self.id_number}"



# Create your models here.
