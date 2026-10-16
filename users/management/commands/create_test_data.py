from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from courses.models import Course, Lesson
from users.models import Payment

User = get_user_model()

class Command(BaseCommand):
    help = 'Создаёт тестовые данные для LMS: пользователи, курсы, уроки, платежи'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # Преподаватель (владелец курса и уроков)
        teacher, _ = User.objects.get_or_create(
            email='teacher1@example.com',
            defaults={
                'password': make_password('password123'),
                'phone': '+79990000010',
                'city': 'Казань',
                'is_active': True,
            }
        )

        # Студенты
        user1, _ = User.objects.get_or_create(
            email='student1@example.com',
            defaults={
                'password': make_password('password123'),
                'phone': '+79990000001',
                'city': 'Москва',
                'is_active': True
            }
        )
        user2, _ = User.objects.get_or_create(
            email='student2@example.com',
            defaults={
                'password': make_password('password123'),
                'phone': '+79990000002',
                'city': 'Санкт-Петербург',
                'is_active': True
            }
        )

        # Курс — с owner
        course, _ = Course.objects.get_or_create(
            title='Django для начинающих',
            owner=teacher,
            defaults={'description': 'Полный курс по Django и DRF'}
        )

        # Уроки — теперь тоже с owner
        lesson1, _ = Lesson.objects.get_or_create(
            course=course,
            title='Введение и установка',
            owner=teacher,  # <-- обязательно
            defaults={'description': 'Как установить Django', 'video_url': 'https://youtube.com/video1'}
        )
        lesson2, _ = Lesson.objects.get_or_create(
            course=course,
            title='Модели и миграции',
            owner=teacher,  # <-- обязательно
            defaults={'description': 'ORM и миграции', 'video_url': 'https://youtube.com/video2'}
        )

        # Платежи
        Payment.objects.get_or_create(
            user=user1,
            paid_course=course,
            paid_lesson=None,
            amount=1500.00,
            payment_method='transfer'
        )
        Payment.objects.get_or_create(
            user=user1,
            paid_course=None,
            paid_lesson=lesson2,
            amount=300.00,
            payment_method='cash'
        )
        Payment.objects.get_or_create(
            user=user2,
            paid_course=course,
            paid_lesson=None,
            amount=1500.00,
            payment_method='transfer'
        )

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
