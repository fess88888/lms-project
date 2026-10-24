from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_youtube_link(value: str):
    """
    Разрешает только ссылки на youtube.com
    """
    if not value:
        return

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        raise ValidationError("Ссылка должна содержать протокол (http/https) и домен.")

    allowed_domains = {"www.youtube.com", "youtube.com"}
    domain = parsed.netloc.lower()

    if domain not in allowed_domains:
        raise ValidationError(
            f"Разрешены только ссылки на YouTube. Указанный домен '{domain}' не поддерживается."
        )
