from django.urls import path
from .views import (
    JobApplyView,
    MyApplicationsView,
    MyJobPostingsView,
    JobApplicationsForOwnerView,
    ApplicationStatusUpdateView
)

urlpatterns = [
    # Worker/Student applies to a job
    path('<int:job_id>/apply/', JobApplyView.as_view(), name='job-apply'),

    # Worker/Student views their applications
    path('my-applications/', MyApplicationsView.as_view(), name='my-applications'),

    # Owner views jobs they posted
    path('my-postings/', MyJobPostingsView.as_view(), name='my-job-postings'),

    # Owner views applications for a specific job
    path('my-postings/<int:job_id>/applications/', JobApplicationsForOwnerView.as_view(), name='job-applications-for-owner'),
    
    # Owner updates application status
    path('<int:pk>/', ApplicationStatusUpdateView.as_view(), name='application-status-update'),

]
