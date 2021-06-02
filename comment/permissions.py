from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    message = 'You must be the owner or admin to update.'

    def safe_methods_or_validated(self, request, func):
        """ 名字和tutorial不一样 """
        if request.method in SAFE_METHODS:
            return True
        return func()

    def has_permission(self, request, view):
        return self.safe_methods_or_validated(
            request,
            lambda: request.user.is_authenticated
        )
    
    def has_object_permission(self, request, view, obj):
        return self.safe_methods_or_validated(
            request,
            lambda: (obj.author == request.user or request.user.is_superuser)
        )