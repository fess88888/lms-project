from rest_framework.views import APIView
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Course, Lesson, Subscription
from .serializers import CourseListSerializer, CourseDetailSerializer, LessonSerializer
from .paginators import StandardResultsSetPagination
from .permissions import ModeratorReadOnlyForCreationAndDeletion


class CourseViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination  # <-- пагинация здесь
    permission_classes = [ModeratorReadOnlyForCreationAndDeletion]

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def get_queryset(self):
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
    pagination_class = StandardResultsSetPagination
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


class ToggleSubscriptionView(generics.GenericAPIView):
    def post(self, request, course_id):
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"message": "Требуется авторизация."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        course = get_object_or_404(Course, pk=course_id)
        subscription_qs = Subscription.objects.filter(user=user, course=course)

        if subscription_qs.exists():
            subscription_qs.delete()
            message = "Подписка удалена"
            is_subscribed = False
            status_code = status.HTTP_200_OK
        else:
            Subscription.objects.create(user=user, course=course)
            message = "Подписка добавлена"
            is_subscribed = True
            status_code = status.HTTP_201_CREATED

        return Response(
            {"message": message, "is_subscribed": is_subscribed},
            status=status_code
        )
