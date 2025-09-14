# projects/permissions.py
from rest_framework import permissions

class CanCreateJob(permissions.BasePermission):
    """
    Only users with role 'owner' or 'company' can create jobs.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role in ['owner', 'company']


class IsJobOwner(permissions.BasePermission):
    """
    Only the user who posted the job can edit or delete it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.posted_by_id == request.user.id
