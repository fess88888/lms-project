from rest_framework import viewsets, generics
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from .permissions import ModeratorReadOnlyForCreationAndDeletion


# Курс: ViewSet полный CRUD (list, create, retrieve, update, partial_update, destroy)
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [ModeratorReadOnlyForCreationAndDeletion]


# Урок: Generic-классы полный CRUD
class LessonListCreateView(generics.ListCreateAPIView):
    """
    GET /api/lessons/ список всех уроков
    POST /api/lessons/ создать урок
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [ModeratorReadOnlyForCreationAndDeletion]


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/lessons/{id}/ один урок
    PUT /api/lessons/{id}/ полное обновление
    PATCH /api/lessons/{id}/ частичное обновление
    DELETE /api/lessons/{id}/ удалить урок
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [ModeratorReadOnlyForCreationAndDeletion]
