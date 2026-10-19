import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_product(name: str) -> dict:
    product = stripe.Product.create(name=name)
    return product

def create_stripe_price(product_id: str, amount_cents: int, currency: str = 'rub') -> dict:
    price = stripe.Price.create(
        product=product_id,
        unit_amount=amount_cents,  # в копейках!
        currency=currency,
    )
    return price

def create_checkout_session(price_id: str, success_url: str, cancel_url: str) -> dict:
    session = stripe.CheckoutSession.create(
        line_items=[
            {
                'price': price_id,
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session


def create_stripe_payment_session(course_id: int, user_id: int) -> dict:
    """
    Создаёт Checkout Session для оплаты курса.
    В реальном проекте price_id лучше брать из модели Course (поле stripe_price_id),
    а не создавать каждый раз.
    """
    from courses.models import Course

    course = Course.objects.get(pk=course_id)
    # Если у курса ещё нет price_id — создаём продукт и цену (для тестов ок, для прода — нет)
    if not hasattr(course, 'stripe_price_id') or not course.stripe_price_id:
        # Создаём продукт
        product = create_stripe_product(course.title)
        # Цена в копейках: например, 1000 руб = 100_000 копеек
        price = create_stripe_price(
            product['id'],
            amount_cents=course.price * 100,  # цена в рублях * 100
            currency='rub',
        )
        course.stripe_price_id = price['id']
        course.save(update_fields=['stripe_price_id'])
        price_id = course.stripe_price_id
    else:
        price_id = course.stripe_price_id

    # URLs должны быть реальными (не localhost для Stripe, но для тестов localhost ок)
    base_url = "http://127.0.0.1:8000"  # в продакшене — реальный домен
    success_url = f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/payment/cancel"

    session = create_checkout_session(
        price_id=price_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return {
        "session_id": session["id"],
        "url": session["url"],
    }
