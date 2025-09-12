from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager


class User(AbstractUser):
    """
    Custom user model supporting multiple roles:
    - Worker: Must have National ID verified and select trades.
    - Company: Must provide company license, registration number, and name.
    - Owner: Similar to company but for individuals or smaller businesses.
    - Student: Add school details later.
    - Admin: Default admin role with extra privileges.
    """

    class Roles(models.TextChoices):
        WORKER = 'worker', _('Worker')
        OWNER = 'owner', _('Owner')
        COMPANY = 'company', _('Company')
        STUDENT = 'student', _('Student')
        ADMIN = 'admin', _('Admin')

    username = None  # Disable default username field
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=Roles.choices)

    # Additional info
    location = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)

    # Company-specific fields
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_license = models.CharField(max_length=50, blank=True, null=True)
    registration_number = models.CharField(max_length=50, blank=True, null=True)

    # Verification
    verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )

    # Ratings for workers
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    # Relationship to National ID
    national_id = models.OneToOneField(
        'NationalID',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user"
    )

    # Required by Django
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone', 'role']

    # Link the custom manager
    objects = CustomUserManager()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    @property
    def is_company_verified(self):
        return self.role == self.Roles.COMPANY and self.verification_status == 'approved'

    @property
    def is_worker_verified(self):
        return self.role == self.Roles.WORKER and self.verified

class Portfolio(models.Model):
    """
    Stores a worker's portfolio, containing images of past projects or work.
    """

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
    """
    Stores official government-issued National IDs.
    Workers registering will be matched and verified against this table.
    """
    id_number = models.CharField(max_length=16, unique=True)
    full_name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.full_name} - {self.id_number}"
