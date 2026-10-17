from rest_framework import permissions
from django.contrib.auth.models import Group

MODERATOR_GROUP_NAME = 'moderators'

class IsModerator(permissions.BasePermission):
    message = 'Требуется роль модератора.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name=MODERATOR_GROUP_NAME).exists()


class ModeratorReadOnlyForCreationAndDeletion(permissions.BasePermission):
    """
    Модератор может: list, retrieve, update, partial_update.
    Но НЕ может: create, destroy.
    """
    message = 'Модераторы не могут создавать или удалять курсы и уроки.'

    def has_permission(self, request, view):
        # Разрешаем все методы, кроме create и destroy
        if request.method in ('POST', 'DELETE'):
            if IsModerator().has_permission(request, view):
                return False
        return True
