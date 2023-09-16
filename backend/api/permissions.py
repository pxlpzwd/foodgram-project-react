from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Model
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.routers import APIRootView


class BlockPermission(BasePermission):
    """Проверка заблокирован ли пользователь."""

    def has_permission(self, request: WSGIRequest, view: APIRootView) -> bool:
        return bool(
            (request.method in SAFE_METHODS)
            or (request.user.is_authenticated and request.user.is_active)
        )


class BaseAuthorStaffPermission(BlockPermission):
    """Базовый класс для совпадения авторов, персонала и только для чтения."""

    def has_object_permission(
        self, request: WSGIRequest, view: APIRootView, obj: Model
    ) -> bool:

        if request.method in SAFE_METHODS:
            return True

        if request.user.is_authenticated and request.user.is_active:
            return self.has_user_permission(request, obj)

        return False

    def has_user_permission(self, request: WSGIRequest, obj: Model) -> bool:
        raise NotImplementedError(
            "Метод `has_user_permission`должен быть переопределен.")


class AuthorStaffOrReadOnly(BaseAuthorStaffPermission):
    """Разрешение на изменение объектов только авторам и администраторам,
       во всех остальных случаях просмотр (только чтение)."""

    def has_user_permission(self, request: WSGIRequest, obj: Model) -> bool:
        return request.user == obj.author or request.user.is_staff


class AdminOrReadOnly(BlockPermission):
    """Разрешение на создание и изменение только админу.
       Остальным только чтение."""

    def has_object_permission(
        self, request: WSGIRequest, view: APIRootView
    ) -> bool:

        return (
            (request.method in SAFE_METHODS)
            or (request.user.is_authenticated
                and request.user.is_active
                and request.user.is_staff)
        )


class OwnerUserOrReadOnly(BaseAuthorStaffPermission):
    """Разрешение на создание и изменение только админу и пользователю.
       Остальным только чтение."""

    def has_user_permission(self, request: WSGIRequest, obj: Model) -> bool:
        return request.user == obj.author or request.user.is_staff
