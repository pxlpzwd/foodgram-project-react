from typing import Optional, Type

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model, Q
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)


class AddDelViewMixin:
    """Добавляет во Viewset дополнительные методы. Содержит методы
       для добавления или удаления объекта связи M2M."""

    add_serializer: Optional[Type[ModelSerializer]] = None
    link_model: Optional[Type[Model]] = None

    def _create_relation(self,
                         obj_id: int | str,
                         relation_type: str) -> Response:
        """Добавляет связь M2M между объектами."""
        obj = get_object_or_404(self.queryset, pk=obj_id)

        # Новый блок здесь:
        if relation_type == 'subscription':
            fields = {'author_id': obj.pk, 'user_id': self.request.user.pk}
        else:
            fields = {'recipe_id': obj.pk, 'user_id': self.request.user.pk}

        try:
            self.link_model.objects.create(**fields)
        except IntegrityError:
            return Response(
                {"error": "Действие уже выполнено."},
                status=HTTP_400_BAD_REQUEST,
            )

        serializer: ModelSerializer = self.add_serializer(obj)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def _delete_relation(self, q: Q) -> Response:
        """Удаляет связь M2M между объектами."""
        try:
            relation = self.link_model.objects.get(
                q & Q(user=self.request.user)
            )
        except ObjectDoesNotExist:
            return Response(
                {"error": f"{self.link_model.__name__} не существует"},
                status=HTTP_400_BAD_REQUEST,
            )

        relation.delete()
        return Response(status=HTTP_204_NO_CONTENT)
