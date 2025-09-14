from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.pagination import PageNumberPagination

from .models import Application
from projects.models import Job
from .serializers import (
    ApplicationCreateSerializer,
    MyApplicationListSerializer,
    ApplicantForOwnerSerializer
)
from .permissions import CanApplyToJob


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for listing endpoints."""
    page_size = 10
    max_page_size = 50
    page_size_query_param = 'page_size'


# ---------------------------
# Apply to a job
# ---------------------------
class JobApplyView(generics.CreateAPIView):
    serializer_class = ApplicationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, CanApplyToJob]

    def get_serializer_context(self):
        job_id = self.kwargs.get('job_id')
        job = get_object_or_404(Job, pk=job_id, status=Job.Status.OPEN)
        return {'request': self.request, 'job': job}


# ---------------------------
# View my applications
# ---------------------------
class MyApplicationsView(generics.ListAPIView):
    serializer_class = MyApplicationListSerializer
    permission_classes = [permissions.IsAuthenticated, CanApplyToJob]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Application.objects.filter(
            applicant=self.request.user
        ).select_related('job').order_by('-created_at')


# ---------------------------
# View my posted jobs and their applicants
# ---------------------------
class MyJobPostingsView(generics.ListAPIView):
    """Lists all jobs posted by the current user with application stats."""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user).annotate(
            total_applications=Count('applications')
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        results = []
        for job in queryset:
            results.append({
                'id': job.id,
                'title': job.title,
                'location': job.location,
                'status': job.status,
                'total_applications': job.total_applications,
            })
        return Response(results)


class JobApplicationsForOwnerView(generics.ListAPIView):
    """Lists all applications for a specific job by its owner."""
    serializer_class = ApplicantForOwnerSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        job = get_object_or_404(Job, pk=job_id)

        if job.posted_by != self.request.user:
            self.permission_denied(
                self.request,
                message="You are not allowed to view applications for this job."
            )

        return Application.objects.filter(job=job).select_related('applicant').order_by('-created_at')
