import stripe
from django.conf import settings
from django.core.management.base import BaseCommand

from courses.models import Course


class Command(BaseCommand):
    help = "Создаёт Stripe Price для всех курсов, у которых его ещё нет"

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.stdout.write("Начинаем создание цен в Stripe...")

        for course in Course.objects.all():
            if course.stripe_price_id:
                self.stdout.write(f"Курс '{course.title}' уже имеет price_id: {course.stripe_price_id}")
                continue

            # Создаём продукт
            product = stripe.Product.create(name=course.title)
            amount_cents = int(course.price * 100)

            price = stripe.Price.create(
                product=product.id,
                unit_amount=amount_cents,
                currency='rub',
            )

            course.stripe_price_id = price.id
            course.save(update_fields=['stripe_price_id'])
            self.stdout.write(
                self.style.SUCCESS(f"Создано: '{course.title}' -> price_id={price.id}")
            )

        self.stdout.write(self.style.SUCCESS("Готово!"))
