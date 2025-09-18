# projects/views.py
from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.pagination import PageNumberPagination
from .models import Job
from .serializers import (
    JobListSerializer,
    JobDetailSerializer,
    JobCreateUpdateSerializer,
    JobSerializer
)
from .permissions import CanCreateJob, IsJobOwner


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# ----------------------------
# List and Create Jobs
# ----------------------------
class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.filter(status=Job.Status.OPEN).select_related('trade', 'posted_by').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['trade__id', 'location', 'status', 'type']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'budget']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(tags=["Projects / Jobs"])
    def get(self, request, *args, **kwargs):
        """
        List all active jobs
        """
        return super().get(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobCreateUpdateSerializer
        return JobListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), CanCreateJob()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save()


# ----------------------------
# Retrieve, Update, Delete a Job
# ----------------------------
class JobRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all().select_related('trade', 'posted_by')
    lookup_field = 'id'

    @swagger_auto_schema(tags=["Projects / Jobs"])
    def get(self, request, *args, **kwargs):
        """
        Retrieve, Update, Delete a Job
        """
        return super().get(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return JobCreateUpdateSerializer
        return JobDetailSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated(), IsJobOwner()]
        return [permissions.AllowAny()]

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


# ----------------------------
# My Job Postings
# ----------------------------
# My Job Postings View
class MyJobPostingsView(generics.ListAPIView):
    """
    View to list all jobs posted by the current authenticated project owner.
    """
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(tags=["Projects / Jobs"],
                         operation_summary="List My Job Postings",
                         operation_description="Returns a list of jobs posted by the authenticated project owner.")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return only jobs posted by the logged-in user.
        When Swagger is generating schema, return an empty queryset to avoid DB issues.
        """
        if getattr(self, 'swagger_fake_view', False):  # Swagger docs view
            return Job.objects.none()
        return Job.objects.filter(posted_by=self.request.user)

    def get_serializer_class(self):
        """
        Explicitly return JobSerializer, including during Swagger schema generation.
        """
        return JobSerializer