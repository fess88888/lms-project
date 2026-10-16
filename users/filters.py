import django_filters
from .models import Payment


class PaymentFilter(django_filters.FilterSet):
    paid_course = django_filters.NumberFilter(field_name='paid_course', lookup_expr='exact')
    paid_lesson = django_filters.NumberFilter(field_name='paid_lesson', lookup_expr='exact')
    payment_method = django_filters.ChoiceFilter(
        field_name='payment_method',
        choices=Payment.PAYMENT_METHOD_CHOICES
    )

    class Meta:
        model = Payment
        fields = []
