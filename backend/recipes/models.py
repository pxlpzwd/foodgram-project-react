from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from PIL import Image

from core.validators import AlphabetValidator, HexColorValidator

User = get_user_model()


class Tag(models.Model):
    """Модель тэгов, которые могут быть назначены рецептам."""
    name = models.CharField(
        "Тэг",
        max_length=64,
        validators=(AlphabetValidator(field="Название тэга"),),
        unique=True,
    )
    color = models.CharField("Цвет",
                             max_length=7,
                             unique=True,
                             validators=[HexColorValidator()]
                             )
    slug = models.CharField("Слаг тэга", max_length=64, unique=True)

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} (цвет: {self.color})"

    def clean(self) -> None:
        """Очистка и валидация полей модели Tag перед сохранением."""
        self.name = self.name.strip().lower()
        self.slug = self.slug.strip().lower()
        self.color = HexColorValidator().normalize_value(self.color)
        super().clean()


class Ingredient(models.Model):
    """Модель ингредиентов, используемых в рецептах."""
    name = models.CharField("Ингридиент", max_length=64)
    measurement_unit = models.CharField("Единицы измерения", max_length=24)

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Ингридиенты"
        ordering = ("name",)
        constraints = (
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_for_ingredient"
            ),
            models.CheckConstraint(
                check=Q(name__length__gt=0),
                name="%(app_label)s_%(class)s_name_is_empty"
            ),
            models.CheckConstraint(
                check=Q(measurement_unit__length__gt=0),
                name="%(app_label)s_%(class)s_measurement_unit_is_empty"
            ),
        )

    def __str__(self) -> str:
        return f"{self.name} {self.measurement_unit}"

    def clean(self) -> None:
        """Очистка и нормализация полей модели перед сохранением."""
        self.name = self.name.lower()
        self.measurement_unit = self.measurement_unit.lower()
        super().clean()


class Recipe(models.Model):
    """Модель рецепта, содержащая информацию о блюде и его составляющих."""
    name = models.CharField("Название блюда", max_length=64)
    author = models.ForeignKey(
        User,
        verbose_name="Автор рецепта",
        related_name="recipes",
        on_delete=models.SET_NULL,
        null=True,
    )
    tags = models.ManyToManyField(Tag, related_name="recipes")
    ingredients = models.ManyToManyField(
        Ingredient, related_name="recipes", through="AmountIngredient"
    )
    pub_date = models.DateTimeField("Дата публикации",
                                    auto_now_add=True,
                                    editable=False)
    image = models.ImageField("Изображение блюда",
                              upload_to="recipe_images/")
    text = models.TextField("Описание блюда", max_length=5000)
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления",
        default=0,
        validators=(
            MinValueValidator(1, "Ваше блюдо готово!",),
            MaxValueValidator(300, "Слишком долго ждать!",),
        ),
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)
        constraints = (
            models.UniqueConstraint(fields=("name", "author"),
                                    name="unique_for_author"),
            models.CheckConstraint(
                check=Q(name__length__gt=0),
                name="%(app_label)s_%(class)s_name_is_empty"
            ),
        )

    def __str__(self) -> str:
        return f"{self.name}. Автор: {self.author.username}"

    def clean(self) -> None:
        """Проводит очистку и предварительную обработку данных перед
           сохранением объекта. Данный метод автоматически обрабатывает
           имя блюда, делает его с заглавной буквы."""
        self.name = self.name.capitalize()
        super().clean()

    def save(self, *args, **kwargs) -> None:
        """Сохраняет изменения объекта модели рецепта в базе данных.
           Перед сохранением ресайзит изображение рецепта до размеров
           500x500 пикселей."""
        super().save(*args, **kwargs)
        image = Image.open(self.image.path)
        image.thumbnail((500, 500))
        image.save(self.image.path)

    def delete(self, *args, **kwargs):
        """Удаляет картинку при удаление рецепта."""
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


class AmountIngredient(models.Model):
    """Модель, отвечающая за количество ингредиентов в каждом рецепте."""
    recipe = models.ForeignKey(Recipe,
                               verbose_name="В каких рецептах",
                               related_name="ingredient",
                               on_delete=models.CASCADE
                               )
    ingredients = models.ForeignKey(Ingredient,
                                    verbose_name="Связанные ингредиенты",
                                    related_name="recipe",
                                    on_delete=models.CASCADE
                                    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        default=0,
        validators=(
            MinValueValidator(1, "Нужно хоть какое-то количество.",),
            MaxValueValidator(32, "Слишком много!",),
        ),
    )

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Количество ингридиентов"
        ordering = ("recipe",)
        constraints = (
            models.UniqueConstraint(
                fields=("recipe", "ingredients"),
                name="%(app_label)s_%(class)s_ingredient_already_added"
            ),
        )

    def __str__(self) -> str:
        return f"{self.amount} {self.ingredients}"


class Favorites(models.Model):
    """Модель для избранных рецептов, связывающая их с пользователем."""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Понравившийся рецепт",
        related_name="in_favorites",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        related_name="favorites",
        on_delete=models.CASCADE
    )
    date_added = models.DateTimeField("Дата добавления",
                                      auto_now_add=True,
                                      editable=False
                                      )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        constraints = (
            models.UniqueConstraint(
                fields=("recipe", "user"),
                name="%(app_label)s_%(class)s_recipe_is_favorite_already"),
        )

    def __str__(self) -> str:
        return f"{self.user} -> {self.recipe}"


class Carts(models.Model):
    """Модель для списка покупок рецептов, связывающая
       рецепты с их владельцами."""
    recipe = models.ForeignKey(Recipe,
                               verbose_name="Рецепты в списке покупок",
                               related_name="in_carts",
                               on_delete=models.CASCADE
                               )
    user = models.ForeignKey(User,
                             verbose_name="Владелец списка",
                             related_name="carts",
                             on_delete=models.CASCADE
                             )
    date_added = models.DateTimeField("Дата добавления",
                                      auto_now_add=True,
                                      editable=False
                                      )

    class Meta:
        verbose_name = "Рецепт в списке покупок"
        verbose_name_plural = "Рецепты в списке покупок"
        constraints = (
            models.UniqueConstraint(
                fields=("recipe", "user"),
                name="%(app_label)s_%(class)s_recipe_is_cart_already"),
        )

    def __str__(self) -> str:
        return f"{self.user} -> {self.recipe}"
