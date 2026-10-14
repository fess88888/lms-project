from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    course_title = serializers.ReadOnlyField(source='paid_course.title')
    lesson_title = serializers.ReadOnlyField(source='paid_lesson.title')

    class Meta:
        model = Payment
        fields = [
            'id',
            'user',
            'user_email',
            'paid_course',
            'course_title',
            'paid_lesson',
            'lesson_title',
            'amount',
            'payment_date',
            'payment_method',
        ]
