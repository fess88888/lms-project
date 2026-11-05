from rest_framework import permissions
from rest_framework.permissions import BasePermission

MODERATOR_GROUP_NAME = 'moderators'

class IsModerator(permissions.BasePermission):
    message = 'Требуется роль модератора.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name=MODERATOR_GROUP_NAME).exists()


class ModeratorReadOnlyForCreationAndDeletion(permissions.BasePermission):
    """
    Модератор НЕ может создавать или удалять.
    Остальные могут, если есть другие проверки (например, владелец курса).
    """
    message = 'Модераторы не могут создавать или удалять курсы и уроки.'

    def has_permission(self, request, view):
        if request.method in ('POST', 'DELETE'):
            if IsModerator().has_permission(request, view):
                return False
        return True


class LessonOwnerOrModeratorReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Разрешаем POST/PUT/PATCH/DELETE только авторизованным
        if request.user and request.user.is_authenticated:
            return True

        if request.method == 'GET':
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # obj — это Lesson
        user = request.user
        if not user.is_authenticated:
            return False

        # Владелец курса может управлять уроками этого курса
        if obj.course.owner == user:
            return True

        if user.groups.filter(name='moderator').exists():
            return True

        if getattr(user, 'is_moderator', False):
            return True

        return False

