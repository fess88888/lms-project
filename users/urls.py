from django.urls import path
from .views import PaymentListView, RegisterView, UserListView, UserDetailView

urlpatterns = [
    path('payments/', PaymentListView.as_view(), name='payment-list'),
    path('register/', RegisterView.as_view(), name='register'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]
