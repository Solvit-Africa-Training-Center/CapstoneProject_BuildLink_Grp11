# projects/views.py
from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Job
from .serializers import (
    JobListSerializer,
    JobDetailSerializer,
    JobCreateUpdateSerializer
)
from .permissions import CanCreateJob, IsJobOwner
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# List and Create Jobs
class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.filter(status=Job.Status.OPEN).select_related('trade', 'posted_by').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['trade__id', 'location', 'status', 'type']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'budget']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination

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


# Retrieve, Update, Delete a Job
class JobRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all().select_related('trade', 'posted_by')
    lookup_field = 'id'

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
