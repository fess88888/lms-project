import logging

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import (
    OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema,
)
from rest_framework import generics, status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Payment

from .models import Course, Lesson, Payment, Subscription
from .paginators import StandardResultsSetPagination
from .permissions import (
    LessonOwnerOrModeratorReadOnly, ModeratorReadOnlyForCreationAndDeletion,
)
from .serializers import (
    CourseDetailSerializer, CourseListSerializer, LessonSerializer,
    PaymentRequestSerializer, PaymentResponseSerializer,
    ToggleSubscriptionResponseSerializer,
)
from .services import create_stripe_payment_session
from .services.stripe_service import create_checkout_session
from .tasks import notify_course_updated


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

        course = get_object_or_404(Course, pk=course_id)
        notify_course_updated.delay(course.id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [LessonOwnerOrModeratorReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()
        return Lesson.objects.all().order_by('id')

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.course.owner != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Вы не можете удалять уроки чужих курсов.')
        instance.delete()
        notify_course_updated.delay(instance.course.id)


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


logger = logging.getLogger(__name__)

class CreatePaymentView(GenericAPIView):
    serializer_class = PaymentRequestSerializer  # <-- это убирает предупреждение в логах

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        course_id = serializer.validated_data["course_id"]
        course = get_object_or_404(Course, pk=course_id)

        if course.price <= 0:
            return Response(
                {"detail": "Курс должен иметь положительную цену."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success_url = getattr(
            settings,
            "STRIPE_SUCCESS_URL",
            "http://127.0.0.1:8000/payment/success",
        )
        cancel_url = getattr(
            settings,
            "STRIPE_CANCEL_URL",
            "http://127.0.0.1:8000/payment/cancel",
        )

        try:
            session = create_checkout_session(course, request.user, success_url, cancel_url)

            payment = Payment.objects.create(
                user=request.user,
                course=course,
                stripe_session_id=session.id,
                status="pending",
                # amount/currency — только если они есть в модели Payment!
            )

            response_data = {
                "session_id": session.id,
                "url": session.url,
                "payment_id": str(payment.id),
                "course_title": course.title,
                "amount": float(course.price),
                "currency": "RUB",
            }

            response_serializer = PaymentResponseSerializer(data=response_data)
            if not response_serializer.is_valid():
                logger.warning("Serializer validation failed: %s", response_serializer.errors)
                return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning("Validation/logic error during payment creation: %s", e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Stripe error or unexpected failure: %s", e)
            return Response(
                {"detail": "Ошибка платёжной системы. Попробуйте позже."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            logger.exception("Stripe error while retrieving session: %s", e)
            return Response(
                {"detail": "Не удалось получить статус сессии от Stripe"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            return Response(
                {"detail": "Недопустимый session_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        status_map = {
            "paid": "paid",
            "canceled": "canceled",
            "expired": "expired",
            "open": "pending",
        }
        mapped_status = status_map.get(session.payment_status, "pending")

        Payment.objects.filter(stripe_session_id=session_id).update(status=mapped_status)

        return Response({
            "session_id": session_id,
            "status": session.payment_status,
            "mapped_status": mapped_status,
            "mode": session.mode,
            "url": session.url if session.mode == "payment" else None,
        })


@csrf_exempt
def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        return render(request, "payment/error.html", {"message": "Не передан session_id"})

    payment = get_object_or_404(Payment, stripe_session_id=session_id)

    if payment.status == "pending":
        payment.status = "paid"
        payment.save()

    return render(
        request,
        "payment/success.html",
        {
            "payment_id": payment.id,
            "course_title": payment.course.title,
            "amount": payment.course.price,
        },
    )

@csrf_exempt
def payment_cancel(request):
    return render(
        request,
        "payment/cancel.html",
        {"message": "Оплата отменена. Вы можете вернуться к выбору курса."}
    )
