from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Course, Lesson, Subscription, Payment
from .serializers import CourseListSerializer, CourseDetailSerializer, LessonSerializer, PaymentRequestSerializer, \
    PaymentResponseSerializer
from .paginators import StandardResultsSetPagination
from .permissions import ModeratorReadOnlyForCreationAndDeletion, LessonOwnerOrModeratorReadOnly
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse
from rest_framework.generics import GenericAPIView
from .serializers import PaymentRequestSerializer, PaymentResponseSerializer
from .services import create_stripe_payment_session
from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from .models import Course, Subscription
from .serializers import ToggleSubscriptionResponseSerializer


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
        return Course.objects.all().order_by('id')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [LessonOwnerOrModeratorReadOnly]  # <-- заменили permission

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def create(self, request, *args, **kwargs):
        """
        Переопределяем create, чтобы проверить: владелец курса может создавать уроки.
        """
        course_id = request.data.get('course')
        if not course_id:
            return Response(
                {'course': ['Это поле обязательно.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        course = get_object_or_404(Course, pk=course_id)
        user = request.user

        # Проверка: только владелец курса может создавать уроки
        if course.owner != user:
            return Response(
                {'detail': 'Вы можете создавать уроки только для своих курсов.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [LessonOwnerOrModeratorReadOnly]  # <-- тоже меняем

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()
        return Lesson.objects.all().order_by('id')

    # Важно: для DELETE проверку владельца курса делаем здесь
    def perform_destroy(self, instance):
        user = self.request.user
        if instance.course.owner != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Вы не можете удалять уроки чужих курсов.')
        instance.delete()


@extend_schema(
    description="Переключение подписки на курс: создание или удаление подписки.",
    parameters=[
        OpenApiParameter(
            name="course_id",
            description="ID курса, на который подписываемся/отписываемся",
            required=True,
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
        )
    ],
    responses={
        200: {"description": "Подписка удалена"},
        201: {"description": "Подписка создана"},
        401: {"description": "Требуется авторизация"},
    },
)
class ToggleSubscriptionView(generics.GenericAPIView):
    serializer_class = ToggleSubscriptionResponseSerializer  # <-- обязательно

    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        if not course_id:
            return Response(
                {"message": "course_id обязателен в URL."},
                status=status.HTTP_400_BAD_REQUEST
            )

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


class CreatePaymentView(GenericAPIView):
    serializer_class = PaymentRequestSerializer

    @extend_schema(
        request=PaymentRequestSerializer,
        responses={
            200: PaymentResponseSerializer,
            400: OpenApiResponse(description="Ошибка валидации"),
            401: OpenApiResponse(description="Требуется авторизация"),
        },
        description="Создать платёжную сессию Stripe для курса",
    )
    def post(self, request, *args, **kwargs):
        # валидация входных данных через сериализатор
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course_id = serializer.validated_data["course_id"]
        user = request.user

        try:
            session_data = create_stripe_payment_session(course_id, user)
            # session_data — это dict от Stripe (session_id, url и т. д.)
            response_serializer = PaymentResponseSerializer(data=session_data)
            response_serializer.is_valid()  # можно raise_exception=False и вернуть ошибки
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
