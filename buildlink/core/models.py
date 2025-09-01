from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _



# User Model

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



# National ID (Demo verification table)

class NationalID(models.Model):
    id_number = models.CharField(max_length=16, unique=True)
    full_name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.full_name} - {self.id_number}"



# Trades

class Trade(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class WorkerTrade(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="worker_trades")
    trade = models.ForeignKey("Trade", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.trade.name}"




# Jobs

class Job(models.Model):
    class JobType(models.TextChoices):
        JOB = 'job', _('Job')
        INTERNSHIP = 'internship', _('Internship')

    class Status(models.TextChoices):
        OPEN = 'open', _('Open')
        CLOSED = 'closed', _('Closed')

    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=JobType.choices)
    trade = models.ForeignKey(Trade, on_delete=models.SET_NULL, null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.type}"



# Applications

class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'applicant')

    def __str__(self):
        return f"{self.applicant.full_name} applied to {self.job.title}"



# Portfolio

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



# Ratings

class Rating(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating} by {self.rater.full_name} to {self.rated_user.full_name}"



# Government Projects

class GovernmentProject(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    permit_id = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



# Notifications

class Notification(models.Model):
    class Status(models.TextChoices):
        SENT = 'sent', _('Sent')
        FAILED = 'failed', _('Failed')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To {self.user.full_name}: {self.message[:20]}..."

