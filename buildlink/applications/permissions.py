from rest_framework import permissions


class CanApplyToJob(permissions.BasePermission):
    """Only workers and students can apply for jobs."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['worker', 'student']

class IsApplicationJobOwner(permissions.BasePermission):
    """
    Only the owner of the related job can act on an application object
    (e.g., update status).
    """

    def has_object_permission(self, request, view, obj):
        # obj is an Application
        return getattr(obj, 'job', None) and obj.job.posted_by_id == request.user.id