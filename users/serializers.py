
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import Payment, User


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


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['email', 'phone', 'city', 'password']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            city=validated_data.get('city', '')
        )
        return user


class PaymentInlineSerializer(serializers.ModelSerializer):
    course_title = serializers.ReadOnlyField(source='paid_course.title', allow_null=True)
    lesson_title = serializers.ReadOnlyField(source='paid_lesson.title', allow_null=True)

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_date', 'payment_method', 'course_title', 'lesson_title']


class UserProfileSerializer(serializers.ModelSerializer):
    payments = PaymentInlineSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone',
            'city',
            'avatar',
            'payments',
        ]


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'city']

