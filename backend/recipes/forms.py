from django.forms import ModelForm
from django.forms.widgets import TextInput

from recipes.models import Tag


class TagForm(ModelForm):
    class Meta:
        model = Tag
        fields = ("name", "color")
        widgets = {
            "color": TextInput(attrs={"type": "color"}),
        }
