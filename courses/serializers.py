from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'owner', 'course', 'title', 'description', 'preview', 'video_url', 'created_at', 'updated_at']
        read_only_fields = ['owner', 'created_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'owner', 'title', 'preview', 'description',
            'lessons', 'lessons_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']

    def get_lessons_count(self, obj):
        return obj.lessons.count()


