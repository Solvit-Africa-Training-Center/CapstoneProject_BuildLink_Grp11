from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.pagination import PageNumberPagination
from .serializers import ApplicationCreateSerializer, MyApplicationListSerializer, ApplicantForOwnerSerializer, ApplicationStatusUpdateSerializer, ApplicationDetailSerializer
from .permissions import CanApplyToJob, IsJobOwner
from drf_yasg.utils import swagger_auto_schema

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
    
    @swagger_auto_schema(tags=["Applications"])
    def post(self, request, job_id=None, *args, **kwargs):
        """
        Apply for a job (workers and students only).
        """
        return super().post(request, *args, **kwargs)

    def get_serializer_context(self):
        
        if getattr(self, 'swagger_fake_view', False):
            return {}
        
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
    
    @swagger_auto_schema(tags=["Applications"])
    def post(self, request, job_id=None, *args, **kwargs):
        """
        View applications.
        """
        return super().post(request, *args, **kwargs)

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
    
    @swagger_auto_schema(tags=["Applications"])
    def post(self, request, job_id=None, *args, **kwargs):
        """
        View my posted jobs and their applicants.
        """
        return super().post(request, *args, **kwargs)
   
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





class ApplicationStatusUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/applications/{application_id}/
    - Only job owner can update the application status.
    """
    queryset = Application.objects.all()
    serializer_class = ApplicationStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsJobOwner]

    def patch(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=kwargs['pk'])

        # Check permissions
        self.check_object_permissions(request, application)

        serializer = self.get_serializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_data = {
            "message": "Application status updated successfully.",
            "application": ApplicationDetailSerializer(application).data
        }
        return Response(response_data, status=status.HTTP_200_OK)