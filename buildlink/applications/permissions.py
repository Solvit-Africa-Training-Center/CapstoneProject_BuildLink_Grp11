from rest_framework import permissions


class CanApplyToJob(permissions.BasePermission):
    """Only workers and students can apply for jobs."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['worker', 'student']


class IsJobOwner(permissions.BasePermission):
    """Only the job owner can view applications for their job."""

    def has_object_permission(self, request, view, obj):
        return obj.posted_by_id == request.user.id




class IsJobOwner(permissions.BasePermission):
    """
    Custom permission to only allow job owners to update an application's status.
    """

    def has_object_permission(self, request, view, obj):
        # The logged-in user must be the owner of the job
        return obj.job.posted_by == request.user