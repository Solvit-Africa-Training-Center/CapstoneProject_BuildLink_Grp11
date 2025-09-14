from rest_framework import permissions


class CanApplyToJob(permissions.BasePermission):
    """Only workers and students can apply for jobs."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['worker', 'student']


class IsJobOwner(permissions.BasePermission):
    """Only the job owner can view applications for their job."""

    def has_object_permission(self, request, view, obj):
        return obj.posted_by_id == request.user.id
