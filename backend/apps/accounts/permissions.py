from django.db.models import Q
from rest_framework.permissions import BasePermission
from .models import Grant


def role_code(user):
    return user.role.code if user.is_authenticated and user.role_id else None


def category_allowed(user, category, operation):
    if not user.is_authenticated or not user.is_active or not user.authorized:
        return False
    if role_code(user) in ('superadmin', 'admin'):
        return True
    return user.categories.filter(pk=category.pk).exists() and Grant.objects.filter(
        Q(user=user) | Q(role_id=user.role_id), category=category, operation=operation).exists()


class AuthorizedAccess(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active and request.user.authorized and bool(request.user.role_id)


class StaffAccess(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active and request.user.authorized and role_code(request.user) in ('admin', 'superadmin')


class SuperAccess(StaffAccess):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and role_code(request.user) == 'superadmin'
