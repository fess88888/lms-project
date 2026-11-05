import os

from django.conf import settings

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("lms_project")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Тестовый режим: задачи выполняются синхронно, без брокера и result-бэкенда.
if os.environ.get("CELERY_TASK_ALWAYS_EAGER", "").lower() == "true":
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    app.conf.task_ignore_result = True

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

