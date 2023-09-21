from collections import OrderedDict

from core.services import recipe_ingredients_set
from core.validators import ingredients_validator, tags_exist_validator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import F, QuerySet
from django.db.transaction import atomic
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, Tag
from rest_framework.serializers import ModelSerializer, SerializerMethodField

User = get_user_model()


class RecipeSummarySerializer(ModelSerializer):
    """Для предоставления краткой информации о рецепте, включая
       его идентификатор, название, изображение и время приготовления."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("__all__",)


class UserSerializer(ModelSerializer):
    """Для работы с данными пользователей, генерации и обработки
       пользовательской информации."""

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "password",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "is_subscribed": {"read_only": True},
        }

    def get_is_subscribed(self, obj: User) -> bool:
        """Проверка подписки пользователей."""
        user = self.context.get("request").user

        if user.is_anonymous or (user == obj):
            return False

        return user.subscriptions.filter(author=obj).exists()

    def create(self, validated_data: dict) -> User:
        """Создаёт нового пользователя с запрошенными полями."""
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserSubscribeSerializer(UserSerializer):
    """Сериализатор вывода авторов на которых подписан текущий пользователь."""

    recipes = RecipeSummarySerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        read_only_fields = ("__all__",)

    def get_is_subscribed(*args) -> bool:
        """Проверка подписки."""
        return True

    def get_recipes_count(self, obj: User) -> int:
        """Показывает общее количество рецептов у каждого автора."""
        return obj.recipes.count()


class TagSerializer(ModelSerializer):
    """Вывод тэгов."""
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")
        read_only_fields = ("id",)

    def validate(self, data: OrderedDict) -> OrderedDict:
        """Удаление пробелов и символов, преобразование к верхнему регистру"""
        for attr, value in data.items():
            data[attr] = value.strip(" #").upper()

        return data


class IngredientSerializer(ModelSerializer):
    """Сериализатор для вывода ингридиентов."""

    class Meta:
        model = Ingredient
        fields = "__all__"
        read_only_fields = ("all",)


class RecipeSerializer(ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = (
            "is_favorite",
            "is_shopping_cart",
        )

    def get_ingredients(self, recipe: Recipe) -> QuerySet[dict]:
        """Получает список ингридиентов для рецепта."""
        ingredients = recipe.ingredients.values(
            "id", "name", "measurement_unit", amount=F("recipe__amount")
        )
        return ingredients

    def get_is_favorited(self, recipe: Recipe) -> bool:
        """Есть ли рецепт в избранном."""
        user = self.context.get("view").request.user

        if user.is_anonymous:
            return False

        return user.favorites.filter(recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe: Recipe) -> bool:
        """Есть ли рецепт в списке покупок."""
        user = self.context.get("view").request.user

        if user.is_anonymous:
            return False

        return user.carts.filter(recipe=recipe).exists()

    def validate_tags(self, tags_ids: list):
        """ Валидация списка идентификаторов тегов."""
        if not tags_ids:
            raise ValidationError("Теги обязательны для создания рецепта.")

        tags = Tag.objects.filter(id__in=tags_ids)
        
        if len(tags) != len(tags_ids):
            raise ValidationError("Указан несуществующий тег.")

        return list(tags)

    def validate_ingredients(self, ingredients: list):
        """Валидация списка ингредиентов."""
        if not ingredients:
            raise ValidationError("Ингредиенты обязательны для создания рецепта.")

        valid_ings = {}

        for ing in ingredients:
            amount = ing.get("amount")

            if not (isinstance(amount, int) or str(amount).isdigit()):
                raise ValidationError("Некорректное количество ингредиента")

            ing_id = ing["id"]
            amount = int(amount)

            if amount <= 0:
                raise ValidationError("Некорректное количество ингредиента")
            valid_ings[ing_id] = amount

        if not valid_ings:
            raise ValidationError("Некорректные ингредиенты")

        db_ings = Ingredient.objects.filter(pk__in=valid_ings.keys())

        if not db_ings:
            raise ValidationError("Некорректные ингредиенты")

        result = {ing.pk: (ing, valid_ings[ing.pk]) for ing in db_ings}
        return result

    def validate(self, data: OrderedDict) -> OrderedDict:
        """Валидация исходных данных."""
        tags_ids: list[int] = self.initial_data.get("tags")
        ingredients = self.initial_data.get("ingredients")
        
        tags = self.validate_tags(tags_ids)
        ingredients = self.validate_ingredients(ingredients)

        data.update(
            {
                "tags": tags,
                "ingredients": ingredients,
                "author": self.context.get("request").user,
            }
        )
        return data

    @atomic
    def create(self, validated_data: dict) -> Recipe:
        """Создаёт рецепт."""
        tags: list[int] = validated_data.pop("tags")
        ingredients: dict[int, tuple] = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe_ingredients_set(recipe, ingredients)
        return recipe

    @atomic
    def update(self, recipe: Recipe, validated_data: dict):
        """Обновляет рецепт."""
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")

        for key, value in validated_data.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            recipe_ingredients_set(recipe, ingredients)

        recipe.save()
        return recipe
