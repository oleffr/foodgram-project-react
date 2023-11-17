from rest_framework import permissions


class AuthorOrAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, object):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_staff or object.author == request.user)