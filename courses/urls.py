from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CourseViewSet, CreatePaymentView, LessonDetailView, LessonListCreateView,
    PaymentStatusView, ToggleSubscriptionView, payment_cancel, payment_success,
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')


urlpatterns = [
    path('courses/<int:course_id>/toggle-subscription/', ToggleSubscriptionView.as_view(), name='course-toggle-subscription'),
    path('', include(router.urls)),
    path('lessons/', LessonListCreateView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('payments/', CreatePaymentView.as_view(), name='payment-create'),
    path(
        "payments/<str:session_id>/status/",
        PaymentStatusView.as_view(),
        name="payment-status",
    ),
    path("payment/success/", payment_success, name="payment_success"),
    path("payment/cancel/", payment_cancel, name="payment_cancel"),
]
