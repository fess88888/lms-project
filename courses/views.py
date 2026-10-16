from rest_framework import viewsets, generics
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from .permissions import ModeratorReadOnlyForCreationAndDeletion


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [ModeratorReadOnlyForCreationAndDeletion]

    def get_queryset(self):
        # Возвращаем только курсы владельца ИЛИ все, если пользователь модератор
        user = self.request.user
        if not user.is_authenticated:
            return Course.objects.none()
        if user.groups.filter(name='moderators').exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [ModeratorReadOnlyForCreationAndDeletion]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [ModeratorReadOnlyForCreationAndDeletion]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

