from celery import shared_task
from django.utils import timezone
from courses.models import Course, Subscription
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def notify_course_updated(course_id):
    """
    Рассылка подписчикам, если курс не обновлялся более 4 часов.
    """
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return

    now = timezone.now()
    four_hours_ago = now - timezone.timedelta(hours=4)

    # Если обновлялся менее 4 часов назад — не рассылаем
    if course.updated_at and course.updated_at > four_hours_ago:
        return

    subscribers = Subscription.objects.filter(
        course=course,
        is_active=True
    ).select_related('user')

    emails = [sub.user.email for sub in subscribers if sub.user.email]
    if not emails:
        return

    subject = f'Обновление курса: {course.title}'
    message = (
        f'Курс "{course.title}" был обновлён.\n'
        f'Заходите в LMS, чтобы посмотреть новые материалы.'
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
        fail_silently=False,
    )
