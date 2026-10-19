from rest_framework import serializers
from .models import Course, Lesson, Subscription
from .validators import validate_youtube_link
from drf_spectacular.utils import extend_schema_field


class LessonSerializer(serializers.ModelSerializer):
    video_url = serializers.URLField(
        required=False,
        allow_blank=True,
        validators=[validate_youtube_link],
        help_text="Разрешены только ссылки на YouTube (youtube.com)"
    )

    class Meta:
        model = Lesson
        fields = [
            'id', 'owner', 'course', 'title', 'description',
            'preview', 'video_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']


class CourseListSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'owner', 'title', 'preview', 'description',
            'lessons_count', 'is_subscribed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']

    @extend_schema_field({'type': 'integer'})
    def get_lessons_count(self, obj):
        return obj.lessons.count()

    @extend_schema_field({'type': 'boolean'})
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(user=request.user, course=obj).exists()


class CourseDetailSerializer(CourseListSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ['lessons']


class ToggleSubscriptionResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    is_subscribed = serializers.BooleanField()

class PaymentRequestSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()

class PaymentResponseSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    url = serializers.URLField()
