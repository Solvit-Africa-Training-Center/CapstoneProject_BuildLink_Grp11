from django.db import models
from Users.models import User
from trades.models import Trade
from django.utils.translation import gettext_lazy as _

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
    
    
    

class ProjectPermit(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    permit_id = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

# Create your models here.
