from django.contrib.auth.models import AbstractUser
from django.db.models import (BooleanField, CharField,
                              CheckConstraint, DateTimeField, EmailField, F,
                              ForeignKey, Model, Q, UniqueConstraint)
from django.db.models.functions import Length
from django.utils.translation import gettext_lazy as _

from core.validators import AlphabetValidator, MinLenValidator

from .normalizers import NormalizeValidators

from django.db import models

CharField.register_lookup(Length)


class NewUser(AbstractUser, NormalizeValidators):
    """Класс настройки аккаунта."""
    email = EmailField(
        verbose_name="Электронная почта",
        max_length=256,
        unique=True,
        help_text="Максимум 256 символов",
    )
    username = CharField(
        verbose_name="Логин",
        max_length=64,
        unique=True,
        help_text="Максимум 64 символа",
        validators=(
            MinLenValidator(
                min_len=3,
                field="username",
            ),
            AlphabetValidator(field="username"),
        ),
    )
    first_name = CharField(
        verbose_name="Имя",
        max_length=64,
        help_text="Максимум 64 символа",
        validators=(
            AlphabetValidator(
                first_regex="[^а-яёА-ЯЁ -]+",
                second_regex="[^a-zA-Z -]+",
                field="Имя",
            ),
        ),
    )
    last_name = CharField(
        verbose_name="Фамилия",
        max_length=64,
        help_text="Максимум 64 символа",
        validators=(
            AlphabetValidator(
                first_regex="[^а-яёА-ЯЁ -]+",
                second_regex="[^a-zA-Z -]+",
                field="Фамилия",
            ),
        ),
    )
    password = CharField(
        verbose_name=_("Пароль"),
        max_length=128,
        help_text="Максимум 128 символов",
    )
    is_active = BooleanField(
        verbose_name="Активирован",
        default=True,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)
        constraints = (
            CheckConstraint(
                check=Q(username__length__gte=3),
                name="\nusername is too short\n",
            ),
        )

    def __str__(self) -> str:
        return f"{self.username}: {self.email}"


class Subscriptions(Model):

    author = ForeignKey(
        verbose_name="Автор рецепта",
        related_name="subscribers",
        to=NewUser,
        on_delete=models.CASCADE,
    )
    user = ForeignKey(
        verbose_name="Подписчики",
        related_name="subscriptions",
        to=NewUser,
        on_delete=models.CASCADE,
    )
    date_added = DateTimeField(
        verbose_name="Дата подписки",
        auto_now_add=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = (
            UniqueConstraint(
                fields=("author", "user"),
                name="\nRepeat subscription\n",
            ),
            CheckConstraint(
                check=~Q(author=F("user")), name="\nNo self sibscription\n"
            ),
        )

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.author.username}"
