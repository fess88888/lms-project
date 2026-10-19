from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from .models import Course, Lesson, Subscription

User = get_user_model()


class LMSAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Группы
        self.moderators_group, _ = Group.objects.get_or_create(name='moderators')

        # Пользователи: только email и password, без username
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='123',
        )
        self.owner.groups.add(self.moderators_group)

        self.user = User.objects.create_user(
            email='user@example.com',
            password='123',
        )

        self.moderator = User.objects.create_user(
            email='moderator@example.com',
            password='123',
        )
        self.moderator.groups.add(self.moderators_group)

        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='123',
        )

        # Курс
        self.course = Course.objects.create(
            owner=self.owner,
            title='Test Course',
            description='Course description',
        )

        # Урок
        self.lesson = Lesson.objects.create(
            owner=self.owner,
            course=self.course,
            title='Lesson 1',
            description='First lesson',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        )

    def _auth_as(self, user):
        self.client.force_authenticate(user=user)

    # Дальше все тесты остаются без изменений, кроме тех, где ты явно использовал username
    # (в DRF force_authenticate и в payload API username обычно не нужен)

    def test_list_lessons_authenticated_owner(self):
        self._auth_as(self.owner)
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_list_lessons_anonymous_returns_empty(self):
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_lesson_owner_success(self):
        self._auth_as(self.owner)
        payload = {
            'title': 'Lesson 2',
            'description': 'Second lesson',
            'course': self.course.id,
            'video_url': 'https://www.youtube.com/watch?v=abc123',
        }
        response = self.client.post('/api/lessons/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Lesson.objects.filter(title='Lesson 2').exists())

    def test_create_lesson_other_user_forbidden(self):
        self._auth_as(self.user)
        payload = {
            'title': 'Lesson Forbidden',
            'description': 'Should not be created',
            'course': self.course.id,
        }
        response = self.client.post('/api/lessons/', payload, format='json')
        self.assertEqual(response.status_code, 403)

    def test_create_lesson_invalid_youtube_link_returns_400(self):
        self._auth_as(self.owner)
        payload = {
            'title': 'Bad Lesson',
            'description': 'Wrong link',
            'course': self.course.id,
            'video_url': 'https://example.com/video',
        }
        response = self.client.post('/api/lessons/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('video_url', response.data)

    def test_retrieve_lesson_success(self):
        self._auth_as(self.owner)
        response = self.client.get(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.lesson.id)

    def test_update_lesson_owner_success(self):
        self._auth_as(self.owner)
        payload = {'title': 'Updated Lesson Title'}
        response = self.client.patch(f'/api/lessons/{self.lesson.id}/', payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lesson.objects.get(id=self.lesson.id).title, 'Updated Lesson Title')

    def test_delete_lesson_owner_success(self):
        self._auth_as(self.owner)
        response = self.client.delete(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_delete_lesson_other_user_forbidden(self):
        self._auth_as(self.user)
        response = self.client.delete(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, 403)

    def test_toggle_subscribe_create(self):
        self._auth_as(self.user)
        response = self.client.post(f'/api/courses/{self.course.id}/subscribe/', {}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())
        self.assertTrue(response.data.get('is_subscribed'))

    def test_toggle_subscribe_remove(self):
        Subscription.objects.create(user=self.user, course=self.course)
        self._auth_as(self.user)
        response = self.client.post(f'/api/courses/{self.course.id}/subscribe/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())
        self.assertFalse(response.data.get('is_subscribed'))

    def test_toggle_subscribe_unauthenticated_returns_401(self):
        response = self.client.post(f'/api/courses/{self.course.id}/subscribe/', {}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_subscription_appears_in_course_list(self):
        Subscription.objects.create(user=self.user, course=self.course)
        self._auth_as(self.user)

        response = self.client.get('/api/courses/')
        self.assertEqual(response.status_code, 200)

        results = response.data.get('results', [])
        course_data = next((c for c in results if c.get('id') == self.course.id), None)

        if course_data is None:
            next_url = response.data.get('next')
            while next_url:
                resp = self.client.get(next_url)
                results = resp.data.get('results', [])
                course_data = next((c for c in results if c.get('id') == self.course.id), None)
                if course_data:
                    break
                next_url = resp.data.get('next')

        self.assertIsNotNone(course_data, f"Course {self.course.id} not found in courses list")
        self.assertTrue(course_data.get('is_subscribed', False))

    def test_moderator_can_list_all_lessons(self):
        self._auth_as(self.moderator)
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_user_sees_only_own_lessons(self):
        self._auth_as(self.user)
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)
