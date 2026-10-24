from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def deactivate_inactive_users():
    """
    Блокирует пользователей, которые не заходили более месяца.
    Batch-обновление одним SQL-запросом.
    """
    now = timezone.now()
    one_month_ago = now - timezone.timedelta(days=30)

    qs = User.objects.filter(
        is_active=True,
        last_login__isnull=False,
        last_login__lt=one_month_ago
    )

    count = qs.update(is_active=False)
    return {'deactivated_count': count}
