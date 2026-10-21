from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin,
)
from django.core.validators import RegexValidator
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if 'phone' not in extra_fields:
            extra_fields['phone'] = '+79990000000'
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('email', unique=True)
    phone = models.CharField(
        'телефон',
        max_length=15,
        validators=[RegexValidator(r'^\+?[0-9]{7,15}$', 'Некорректный номер')]
    )
    city = models.CharField('город', max_length=100, blank=True)
    avatar = models.ImageField('аватар', upload_to='avatars/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    objects = UserManager()

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличные'),
        ('transfer', 'Перевод на счёт'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='пользователь'
    )
    paid_course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='course_payments',
        verbose_name='оплаченный курс'
    )
    paid_lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_payments',
        verbose_name='оплаченный урок'
    )
    amount = models.DecimalField(
        'сумма оплаты',
        max_digits=10,
        decimal_places=2
    )
    payment_date = models.DateTimeField(
        'дата оплаты',
        auto_now_add=True
    )
    payment_method = models.CharField(
        'способ оплаты',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='transfer'
    )

    class Meta:
        verbose_name = 'платёж'
        verbose_name_plural = 'платежи'
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.user.email} — {self.amount} ({self.payment_method})"
