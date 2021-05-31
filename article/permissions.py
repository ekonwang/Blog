from rest_framework import permissions

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """ 
    仅管理员可以修改其他用户只能查看
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser