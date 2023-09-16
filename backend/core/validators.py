from re import compile
from string import hexdigits
from typing import TYPE_CHECKING, Dict, List, Tuple, Union

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

if TYPE_CHECKING:
    from recipes.models import Ingredient, Tag


@deconstructible
class AlphabetValidator:
    def __init__(
        self,
        first_regex: str | None = "[^а-яёА-ЯЁ]+",
        second_regex: str | None = "[^a-zA-Z]+",
        field: str | None = "Переданное значение",
    ) -> None:
        self.first_regex = compile(first_regex)
        self.second_regex = compile(second_regex)
        self.field = field
        self.message = f"\n{self.field} <%s> на разных языках либо содержит не только буквы.\n"

    def __call__(self, value: str) -> None:
        if self.first_regex.search(value) and self.second_regex.search(value):
            raise ValidationError(self.message % value)


@deconstructible
class MinLenValidator:
    def __init__(
        self,
        min_len: int | None = 0,
        field: str | None = "Переданное значение",
    ) -> None:
        self.min_len = min_len
        self.field = field
        self.message = f"\n{self.field} недостаточной длины.\n"

    def __call__(self, value: str) -> None:
        if len(value) < self.min_len:
            raise ValidationError(self.message)


def hex_color_validator(color: str) -> str:
    color = color.strip(" #")
    if len(color) not in (3, 6) or not set(color).issubset(hexdigits):
        raise ValidationError(f"Код цвета {color} некорректен.")
    if len(color) == 3:
        color = f"{color[0] * 2}{color[1] * 2}{color[2] * 2}"
    return f"#{color.upper()}"


def tags_exist_validator(tags_ids: List[Union[int, str]], Tag: "Tag") -> List["Tag"]:
    if not tags_ids:
        raise ValidationError("Не указаны тэги")

    tags = Tag.objects.filter(id__in=tags_ids)
    if len(tags) != len(tags_ids):
        raise ValidationError("Указан несуществующий тэг")

    return list(tags)


def ingredients_validator(
    ingredients: List[Dict[str, Union[str, int]]],
    Ingredient: "Ingredient",
) -> Dict[int, Tuple["Ingredient", int]]:
    if not ingredients:
        raise ValidationError("Не указаны ингридиенты")

    valid_ings = {}
    for ing in ingredients:
        amount = ing.get("amount")
        if not (isinstance(amount, int) or str(amount).isdigit()):
            raise ValidationError("Неправильное количество ингидиента")

        ing_id = ing["id"]
        amount = int(amount)
        if amount <= 0:
            raise ValidationError("Неправильное количество ингридиента")

        valid_ings[ing_id] = amount

    if not valid_ings:
        raise ValidationError("Неправильные ингидиенты")

    db_ings = Ingredient.objects.filter(pk__in=valid_ings.keys())
    if not db_ings:
        raise ValidationError("Неправильные ингидиенты")

    result = {ing.pk: (ing, valid_ings[ing.pk]) for ing in db_ings}

    return result