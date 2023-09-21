from re import compile
from string import hexdigits
from typing import TYPE_CHECKING, Dict, List, Tuple, Union

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

if TYPE_CHECKING:
    from recipes.models import Ingredient, Tag


@deconstructible
class HexColorValidator:
    message = "Код цвета некорректен."

    def __call__(self, value: str) -> None:
        color = value.strip(" #")
        if len(color) not in (3, 6) or not set(color).issubset(hexdigits):
            raise ValidationError(self.message, code="invalid", params={"value": value})

    def normalize_value(self, value: str) -> str:
        color = value.strip(" #")
        if len(color) == 3:
           color = f"{color[0] * 2}{color[1] * 2}{color[2] * 2}"
        return f"#{color.upper()}"


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
        self.message = (
            f"\n{self.field} <%s> на разных языках либо "
            f"содержит не только буквы.\n"
        )

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

