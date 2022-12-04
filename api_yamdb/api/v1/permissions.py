from rest_framework import permissions, views
from rest_framework.request import Request


class AdminOnlyPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: views.APIView):
        return request.user.is_authenticated and request.user.is_admin


class IsAuthorAdminModeratorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == 'POST':
            return request.user.is_authenticated
        return request.user.is_authenticated and (
            request.user == obj.author
            or request.user.is_moderator
            or request.user.is_admin
        )


class IsAdminOrReadOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and request.user.is_admin)
            or (request.user.is_authenticated and request.user.is_staff)
        )
