from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, LessonListCreateView, LessonDetailView, ToggleSubscriptionView, CreatePaymentView

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')

urlpatterns = [
    path('courses/<int:course_id>/subscribe/', ToggleSubscriptionView.as_view(), name='course-subscribe'),
    path('', include(router.urls)),
    path('lessons/', LessonListCreateView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('payments/', CreatePaymentView.as_view(), name='payment-create'),
]
