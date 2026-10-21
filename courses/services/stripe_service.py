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

def create_checkout_session(course, user, success_url, cancel_url):
    import stripe
    from django.conf import settings

    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "rub",
                    "unit_amount": int(course.price * 100),
                    "product_data": {"name": course.title},
                },
                "quantity": 1,
            },
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session


def create_stripe_payment_session(course_id: int, user_id: int) -> dict:
    from courses.models import Course

    course = Course.objects.get(pk=course_id)
    if not hasattr(course, 'stripe_price_id') or not course.stripe_price_id:
        product = create_stripe_product(course.title)
        price = create_stripe_price(
            product['id'],
            amount_cents=course.price * 100,
            currency='rub',
        )
        course.stripe_price_id = price['id']
        course.save(update_fields=['stripe_price_id'])
        price_id = course.stripe_price_id
    else:
        price_id = course.stripe_price_id

    base_url = "http://127.0.0.1:8000"

    # ТОЛЬКО базовый URL. Без параметров, без скобок.
    success_url = f"{base_url}/payment/success"
    cancel_url = f"{base_url}/payment/cancel"

    session = create_checkout_session(
        course=course,
        user=None,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return {
        "session_id": session["id"],
        "url": session["url"],
    }
